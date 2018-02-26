import sys
sys.path.insert(0, '.')  # shitty hack.

from flask import Flask
from flask import Flask, request, render_template, redirect, abort, url_for

from tensorflow import gfile
import os

import rl_loop

app = Flask(__name__)


@app.route('/')
def index():
    models = rl_loop.get_models()
    print(models)
    return render_template("index.html", models=[m[1] for m in models])


@app.route("/model/<path:model_name>")
def model_list(model_name):
    games = gfile.Glob(os.path.join(
        rl_loop.SGF_DIR, model_name, 'clean', '*.sgf'))
    return render_template("model.html", files=games, model=model_name)


@app.route("/game/<path:filename>")
def game_view(filename):
    with gfile.GFile(filename, 'r') as f:
        data = f.read()
    return render_template("game.html", data=data)
