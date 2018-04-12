from tensorflow import gfile
import os
import random
from tqdm import tqdm
import multiprocessing as mp
import functools
import itertools
import rl_loop
import dual_net
import subprocess
from utils import timer
import time


# 1 for ZLIB!  Make this match preprocessing.
READ_OPTS = tf.python_io.TFRecordOptions(1)

LOCAL_DIR = "data/"


def pick_examples_from_tfrecord(filename, samples_per_game=4):
    protos = [p for p in
              tf.python_io.tf_record_iterator(filename, READ_OPTS)]
    choices = random.sample(protos, samples_per_game)

    def make_example(protostring):
        e = tf.train.Example()
        e.ParseFromString(protostring)
        return e
    examples = list(map(make_example, choices))
    return examples


def choose(g, samples_per_game=4):
    examples = pick_examples_from_tfrecord(g, samples_per_game)
    t = file_timestamp(g)
    return [(t, ex) for ex in examples]


def file_timestamp(filename):
    return int(os.path.basename(filename).split('-')[0])


class ExampleBuffer():
    def __init__(self, max_size=2000000):
        self.examples = []
        self.max_size = max_size

    def parallel_fill(self, games, threads=8, samples_per_game=4):
        games.sort(key=lambda f: os.path.basename(f))
        if len(games) * samples_per_game > self.max_size:
            games = games[-1 * self.max_size // samples_per_game:]

        f = functools.partial(choose, samples_per_game=samples_per_game)

        with mp.Pool(threads) as p:
             r = tqdm(p.imap(f, games), total=len(games))
             self.examples = list(itertools.chain(*r))

    def update(self, new_games, samples_per_game=4):
        """
        new_games is list of .tfrecord.zz files of new games
        """
        new_games.sort(key=lambda f: os.path.basename(f))
        for game in tqdm(new_games):
            t = file_timestamp(game)
            if t <= self.examples[-1][0]:
                continue
            print("New game:", os.path.basename(game))
            choices = [(t, ex) for ex in pick_examples_from_tfrecord(
                game, samples_per_game)]
            if len(self.examples) > self.max_size:
                self.examples = self.examples[samples_per_game:]
            self.examples.extend(choices)

    def flush(self, path):
        preprocessing.write_tf_examples(path, self.examples)


def files_for_model(model):
    return gfile.Glob(os.path.join(LOCAL_DIR, model[1], '*.zz'))


def smart_rsync(from_model_num=0, source_dir=rl_loop.SELFPLAY_DIR, dest_dir=LOCAL_DIR):
    from_model_num = 0 if from_model_num < 0 else from_model_num
    models = [m for m in rl_loop.get_models() if m[0] >= from_model_num]
    for m in models:
        _ensure_dir_exists(os.path.join(LOCAL_DIR, m[1]))
        subprocess.call(['gsutil', '-m', 'rsync',
                         os.path.join(source_dir, m[1]), os.path.join(dest_dir, m[1])],
                        stderr=open('.rsync_log', 'ab'))


def loop(bufsize=dual_net.EXAMPLES_PER_GENERATION,
         write_dir=rl_loop.TRAINING_CHUNK_DIR,
         model_window=100,
         threads=8,
         skip_first_rsync=False):
    buf = ExampleBuffer(bufsize)

    while True:
        models = rl_loop.get_models()[-model_window:]
        if not skip_first_rsync:
            with timer("Rsync"):
                smart_rsync(models[-1][0] - 6)
        files = list(tqdm(map(files_for_model, models), total=len(models)))
        buf.parallel_fill(list(itertools.chain(*files)))

        print("Filled buffer, watching for new games")

        while rl_loop.get_latest_model()[0] == models[-1][0]:
            with timer("Rsync"):
                smart_rsync(models[-1][0] - 2)
            new_files = list(
                tqdm(map(files_for_model, models[-2:]), total=len(models)))
            buf.update(list(itertools.chain(*new_files)))
            print("Sleeping")
            time.sleep(5*60)
        latest = rl_loop.get_latest_model()

        print("New model!", latest[1], "!=", models[-1][1])
        buf.flush(os.path.join(write_dir, str(latest[0]+1)))


def _ensure_dir_exists(directory):
    if directory.startswith('gs://'):
        return
    os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    argh.dispatch(loop)
    pass
