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
from threading import Lock
import functools

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
               "-v", "2"]

p = subprocess.Popen(GTP_COMMAND,
                     stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)

stdout_thread = None
stdout_thread_lock = Lock()
stderr_thread = None
stderr_thread_lock = Lock()


def std_bg_thread(stream):
    for line in p.__getattribute__(stream):
        print("E -> C ", line)
        socketio.send(str(line), namespace='/' + stream)
        socketio.sleep(0.1)
    print(stream, "bg_thread died")


@socketio.on('connect', namespace='/stdout')
def stdout_connected():
    global stdout_thread
    with stdout_thread_lock:
        if stdout_thread is None:
            stdout_thread = socketio.start_background_task(
                target=functools.partial(std_bg_thread, 'stdout'))
    print("stdout connected")


@socketio.on('connect', namespace='/stderr')
def stderr_connected():
    global stderr_thread
    with stderr_thread_lock:
        if stderr_thread is None:
            stderr_thread = socketio.start_background_task(
                target=functools.partial(std_bg_thread, 'stderr'))
    print("stderr connected")


@socketio.on('connect', namespace='/stdin')
def stdin_connected():
    print("stdin connected")


@socketio.on('message', namespace='/stderr')
def stderr_message(data):
    print(data)


@socketio.on('my event', namespace='/stdin')
def stdin_cmd(message):
    print("C -> E:", message['data'])
    p.stdin.write(bytes(message['data'] + '\r\n', encoding='utf-8'))
    p.stdin.flush()


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
