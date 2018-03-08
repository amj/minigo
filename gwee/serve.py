import sys
sys.path.insert(0, '.')  # to run from minigo/ dir


from flask import Flask, g
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, render_template, redirect, abort, url_for, jsonify, stream_with_context, Response

from flask_socketio import SocketIO

from tensorflow import gfile
import os
from datetime import datetime
from tqdm import tqdm
import subprocess

import main

app = Flask(__name__)
app.config['SECRET_KEY'] = 'woo'
socketio = SocketIO(app)

#TODO(amj) extract to flag
MODEL_PATH = "saved_models/000496-polite-ray-upgrade"
GTP_COMMAND = ["python",  '-u',  # turn off buffering
               "main.py", "gtp",
               "--load-file", MODEL_PATH,
               "--readouts", "1000",
               "-v", "3"]

p = subprocess.Popen(GTP_COMMAND,
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)


@app.route("/stderr-get")
def stderr():
    def stream_stderr(proc):
        for line in proc.stderr:
            yield line
    return Response(stream_with_context(stream_stderr(p)))


@app.route("/stdout-get")
def stdout():
    def stream_stdout(proc):
        for line in proc.stdout:
            yield line
    return Response(stream_with_context(stream_stdout(p)))


@socketio.on('connect', namespace='/stderr')
def stderr_connected():
    print("connected:")


@socketio.on('message', namespace='/stderr')
def stderr_message(data):
    for line in p.stderr:
        print("sending:", line)
        socketio.send(line, namespace='/stderr')


#@app.route('/genmove', method="POST")
#def genmove():
#    if not getattr(g, 'color', None):
#        g.color = 'b'
#    p.stdin.write(bytes("genmove {}\r\n".format(g.color), ))
#    p.stdin.flush()
#
#    g.color = 'w' if g.color == 'b' else 'b'
#    return redirect(url_for('stdout'))


@app.route("/showboard")
def showboard():
    p.stdin.write(b"showboard\r\n")
    p.stdin.flush()
    return redirect(url_for('stderr'))


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == '__main__':
  socketio.run(app)
