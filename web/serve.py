import sys
sys.path.insert(0, '.')  # hack to make it run from minigo/ dir.

from flask import Flask, g
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, render_template, redirect, abort, url_for

from tensorflow import gfile
import os
import re
import sqlite3
from datetime import datetime
from tqdm import tqdm
import shipname

import rl_loop

app = Flask(__name__)
cache = SimpleCache()  # TODO(amj): replace with memcached

DATABASE = 'web/test.db'
EVAL_DIR = os.path.join(rl_loop.BASE_DIR, 'eval')

rl_loop.print_flags()
print("Looking for games in:", EVAL_DIR)


def expected(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def elo(prior, expected, score, k=50):
    return prior + k * (score - expected)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/seed')
def seed_ratings():
    players_w = [p['player_w'] for p in query_db(
        'select player_w from results group by player_w')]
    players_b = [p['player_b'] for p in query_db(
        'select player_b from results group by player_b')]
    p_w_ratings = [row['player'] for row in query_db(
        'select player from ratings group by player')]
    print(p_w_ratings)

    unrated = set(players_w).union(set(players_b)) - set(p_w_ratings)
    print("Getting new rating objs: ", unrated)

    db = get_db()
    for p in unrated:
        db.execute(
            'insert into ratings (player, rating, timestamp) values (?, ?, ?)', (p, 1500, 0))
    db.commit()
    return redirect(url_for('ratings'))


@app.route('/ratings')
def ratings():
    results = [row for row in query_db(
        'select * from ratings order by rating desc')]
    last = query_db(
        'select timestamp from ratings order by timestamp desc', one=True)['timestamp']
    last = datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M")
    return render_template("ratings.html", rows=results, last=last)


@app.route('/rate')
def rate():
    db = get_db()
    last = query_db(
        'select timestamp from ratings order by timestamp desc', one=True)['timestamp']

    ids_by_player = {row['player']: row['id']
                     for row in query_db('select id, player from ratings')}

    ratings = {}
    for row in query_db('select distinct player, timestamp, rating from ratings order by timestamp asc, player desc'):
        ratings[row['player']] = row['rating']

    for row in query_db("select * from results where timestamp > ? order by timestamp asc limit 1000", [last, ]):
        pb = row['player_b']
        pw = row['player_w']
        if row['timestamp'] > last:
            last = row['timestamp']

        res = 1 if row['b_won'] else 0

        ratings[pb] = elo(ratings[pb], expected(ratings[pb], ratings[pw]), res)
        ratings[pw] = elo(ratings[pw], expected(
            ratings[pw], ratings[pb]), 1 if res == 0 else 0)

        print("{} (b) vs {} (w), {}.  b now: {:.2f} w now: {:.2f}".format(
            pb, pw, res, ratings[pb], ratings[pw]))

    for player, rating in ratings.items():
        db.execute('update ratings set (player, rating, timestamp) = (?, ?, ?) where id=?', (
            player, rating, last, ids_by_player[player]))
    db.commit()

    return redirect(url_for('ratings'))


@app.route('/update')
def update_results():
    new_games = gfile.Glob(os.path.join(EVAL_DIR, '*.sgf'))
    db = get_db()
    for f in tqdm(reversed(new_games)):
        with gfile.Open(f, 'r') as _f:
            data = _f.read()
        try:
            w = re.search(r'PW\[([\w-]*)', data).group(1)
            b = re.search(r'PB\[([\w-]*)', data).group(1)
        except:
            print("unknown players:", f)
            continue
        try:
            res = re.search(r'RE\[([wWbB])', data).group(1)
        except:
            print("Unknown result:", f)
            continue

        timestamp = os.path.basename(f).split('-')[0]

        try:
            db.execute('insert into results (player_b, player_w, game_loc, timestamp, b_won) values (?, ?, ?, ?, ?)',
                       (b, w, f, timestamp, res.lower() == 'b'))
            db.commit()
        except:
            print("Caught-up at:", timestamp)
            break

    return redirect(url_for('eval'))


@app.route('/')
def index():
    models = cache.get('models')
    if models is None:
        models = rl_loop.get_models()
        cache.set('models', models, timeout=10*60)
    return render_template("index.html", models=[m[1] for m in models])


@app.route('/eval/<model_name>')
def models_eval_games(model_name):
    if not model_name:
        return redirect(url_for('eval'))

    games = [row for row in query_db(
        'select * from results where player_w = ? or player_b = ? order by timestamp desc',
        (model_name, model_name))]

    won_higher = 0
    vs_higher = 0
    won_lower = 0
    vs_lower = 0
    as_white = 0
    my_num = shipname.detect_model_num(model_name)
    opp_wins = {}
    opp_totals = {}
    for game in games:
        as_white += 1 if game['player_w'] == model_name else 0
        other_player = game['player_w'] if game['player_b'] == model_name else game['player_b']
        i_won = game['b_won'] if game['player_b'] == model_name else not game['b_won']

        opp_totals[other_player] = opp_totals.get(other_player, 0) + 1
        if i_won:
            opp_wins[other_player] = opp_wins.get(other_player, 0) + 1

        if shipname.detect_model_num(other_player) > my_num:
            vs_higher += 1
            if i_won:
                won_higher += 1
        else:
            vs_lower += 1
            if i_won:
                won_lower += 1

    tot_count = len(games)
    won_count = won_higher + won_lower
    assert tot_count == vs_lower + vs_higher

    return render_template("model_eval_gamelist.html", model_name=model_name,
                           games=games, won_count=won_count,
                           won_higher=won_higher,
                           won_lower=won_lower,
                           vs_higher=vs_higher,
                           vs_lower=vs_lower,
                           tot_count=tot_count,
                           opp_totals=opp_totals,
                           opp_wins=opp_wins,
                           as_white=as_white)


@app.route('/eval')
def eval():
    res = [row for row in query_db(
        'select * from results order by timestamp desc')]
    return render_template("results.html", results=res)


@app.route("/games/<path:model_name>")
def game_list(model_name):
    games = cache.get(model_name)
    if games is None:
        games = gfile.Glob(
            os.path.join(rl_loop.SGF_DIR, model_name, 'clean', '*.sgf')
        )
        cache.set(model_name, games, timeout=5*60)
    return render_template("model.html", files=games, model=model_name)


@app.route("/game/<path:filename>")
def game_view(filename):
    with gfile.GFile(filename, 'r') as f:
        data = f.read()
    return render_template("game.html", data=data)
