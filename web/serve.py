import sys
sys.path.insert(0, '.')  # shitty hack.

from flask import Flask
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, render_template, redirect, abort, url_for

from tensorflow import gfile
import os

import rl_loop

app = Flask(__name__)
cache = SimpleCache()  # TODO(amj): replace with memcached


EVAL_DIR = os.path.join(rl_loop.BASE_DIR, 'eval')


@app.route('/')
def index():
    models = cache.get('models')
    if models is None:
        models = rl_loop.get_models()
        cache.set('models', models, timeout=10*60)
    return render_template("index.html", models=[m[1] for m in models])


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
