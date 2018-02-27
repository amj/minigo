import sys
sys.path.insert(0, '.')  # shitty hack.

from flask import Flask, g
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, render_template, redirect, abort, url_for

from tensorflow import gfile
import os
import re
import sqlite3

import rl_loop

app = Flask(__name__)
cache = SimpleCache()  # TODO(amj): replace with memcached

DATABASE = 'web/test.db'
EVAL_DIR = os.path.join(rl_loop.BASE_DIR, 'eval')


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


@app.route('/update')
def update_results():
    new_games = gfile.Glob(os.path.join(EVAL_DIR, '*.sgf'))
    for f in new_games:
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
        db = get_db()
        print("inserting:(player_b, player_w, game_loc, timestamp, b_won)\n( {}, {}, {}, {}, {} )".format(
            w, b, f,
            timestamp,
            res.lower() == 'b'))

        db.execute('insert into results (player_b, player_w, game_loc, timestamp, b_won) values (?, ?, ?, ?, ?)',
                   (w, b, f,
                    timestamp,
                    res.lower() == 'b'))

    db.commit()
    return 'Yay'


@app.route('/')
def index():
    models = cache.get('models')
    if models is None:
        models = rl_loop.get_models()
        cache.set('models', models, timeout=10*60)
    return render_template("index.html", models=[m[1] for m in models])


@app.route('/eval')
def eval():
    res = [row for row in query_db(
        'select * from results order by timestamp desc')]
    return render_template("results.html", results=res)


@app.route("/model/<path:model_name>")
def model_list(model_name):
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
