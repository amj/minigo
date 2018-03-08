import sys
sys.path.insert(0, '.')  # to run from minigo/ dir


from flask import Flask, g
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, render_template, redirect, abort, url_for, jsonify, stream_with_context, Response

from tensorflow import gfile
import os
from datetime import datetime
from tqdm import tqdm
import subprocess

import main

app = Flask(__name__)

#TODO(amj) extract to flag
MODEL_PATH = "gs://minigo-pub/v3-9x9/000496-polite-ray"
GTP_COMMAND = ["python",  '-u',  # turn off buffering
               "main.py", "gtp",
               "--load-file", MODEL_PATH,
               "--readouts", "10000",
               "-v", "3"]

p = subprocess.Popen(GTP_COMMAND,
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)


@app.route("/stdout")
def stdout():
    def get_some_stdout(p):
        for line in p.stderr:
            print(line)
            yield line
    return Response(stream_with_context(get_some_stdout(p)))


@app.route('/genmove')
def genmove():
    if not getattr(g, 'color', None):
        g.color = 'b'
    p.stdin.write(bytes("genmove {}\r\n".format(g.color), ))

    g.color = 'w' if g.color == 'b' else 'b'
    return redirect(url_for('stdout'))


@app.route("/showboard")
def showboard():
    p.stdin.write(b"showboard\r\n")
    p.stdin.flush()
    return redirect(url_for('stdout'))


@app.route("/")
def index():
    return "Hello world!"
