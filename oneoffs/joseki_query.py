# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
sys.path.insert(0, '.')  # nopep8
import logging
import json
import sqlite3
import collections
import datetime as dt

from absl import flags
from flask import Flask, g
from timeit import default_timer as timer
import flask

import oneoffs.opening_freqs_export as ofe

flags.DEFINE_integer("port", 5001, "Port to listen on.")

flags.DEFINE_string("host", "127.0.0.1", "The hostname or IP to listen on.")

FLAGS = flags.FLAGS

# Suppress Flask's info logging.
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

app = Flask(__name__, static_url_path="", static_folder="./")

MIN_PATTERN_LENGTH = 3
DATABASE = '/data/sgf/new_joseki.db.bak'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(seq):
    cur = get_db().execute('''
                     select run, hour, count from joseki_counts
                           where seq_id = (select id from joseki where seq = ?);
                     ''', (seq, ))
    return list(cur.fetchall())

@app.route("/")
def index():
    return app.send_static_file("joseki_search.html")

@app.route("/nexts", methods=["POST"])
def nexts():
    d = json.loads(flask.request.data.decode('utf-8'))
    prefix = d['params']['prefix']
    run = d['params']['run']
    print(prefix, run)

    db = get_db()
    db.set_trace_callback(print)

    res = {'count': 0, 'next_moves': {}}

    s_id = db.execute("select id from joseki where seq=?", (prefix,)).fetchone()
    if not s_id:
        return flask.Response(json.dumps(res), mimetype='text/json')
    else:
        s_id = s_id[0]

    if run is None:
        nexts = db.execute("""
                           select next_move, sum(count) from next_moves where seq_id = ? group by 1
                           """, (s_id,)).fetchall()
        total = db.execute("select sum(count) from joseki_counts where seq_id = ?",
                           (s_id,)).fetchone()[0]
    else:
        start = timer()
        nexts = db.execute("""
                           select next_move, sum(nm.count)
                           from next_moves as nm join joseki_counts as jc
                           on jc.id == nm.joseki_hour_id
                           where nm.seq_id = ? and jc.run = ? group by 1
                           """, (s_id, run)).fetchall()
        end = timer()
        print('%.4f seconds for fancy join.' % (end-start,))
        total = db.execute("select sum(count) from joseki_counts where seq_id = ? and run=?",
                           (s_id, run)).fetchone()[0]

    if not nexts:
        return flask.Response(json.dumps(res), mimetype='text/json')



    next_moves = {}
    tot = 0
    for nxt, ct in nexts:
        next_moves[nxt] = ct
        tot += ct

    for k in next_moves:
        next_moves[k] /= tot

    max_v = max(next_moves.values())

    next_moves = {k:v/max_v for k,v in next_moves.items() if v > 0.001}
    res = {'count': total,
           'next_moves': next_moves}

    return flask.Response(json.dumps(res), mimetype='text/json')


@app.route("/search", methods=["POST"])
def search():
    d = json.loads(flask.request.data.decode('utf-8'))
    print(d)
    sgf = d['params']['sgf']

    query = sgf
    if len(sgf) < MIN_PATTERN_LENGTH:
        print("error")

    print(query)
    print('querying')

    ts = lambda hr: int(dt.datetime.strptime(hr, "%Y-%m-%d-%H").timestamp())
    ranges = ofe.run_time_ranges(get_db())
    interps = ofe.build_run_time_transformers(ranges)

    runs = sorted(ranges.keys())

    cols = []
    cols.append({'id': 'time', 'label': '% of Training', 'type': 'number'})
    for run in runs:
        cols.append({'id': run + 'count', 'label': run + ' times seen', 'type': 'number'})

    data = []
    sequence_counts = query_db(query)
    print(len(sequence_counts))

    rows = collections.defaultdict(lambda: [0 for i in range(len(runs))])

    for r, hr, ct in sequence_counts:
        key = interps[r](ts(hr))
        idx = runs.index(r)
        rows[key][idx] = ct

    row_data = [ {'c': [ {'v': key} ] + [{'v': v if v else None} for v in value ] }
                for key,value in rows.items()]
    obj = {'cols': cols, "rows": row_data, "sequence": query}
    data.append(obj)
    return flask.Response(json.dumps(obj), mimetype='text/json')


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

if __name__ == '__main__':
  absl.app.run(main)
