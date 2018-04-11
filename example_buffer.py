import tensorflow as tf
import os
import random
from tqdm import tqdm
import multiprocessing as mp
import functools


# 1 for ZLIB!  Make this match preprocessing.
READ_OPTS = tf.python_io.TFRecordOptions(1)


def read_tfrecord_to_example_list(filename):
    protos = [p for p in
              tf.python_io.tf_record_iterator(filename, READ_OPTS)]

    def make_example(protostring):
        e = tf.train.Example()
        e.ParseFromString(protostring)
        return e
    examples = list(map(make_example, protos))
    return examples


def choose(g, samples_per_game=4):
    examples = read_tfrecord_to_example_list(g)
    t = file_timestamp(g)
    choices = [(t, s)
               for s in random.sample(examples, samples_per_game)]
    return choices


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
            r = list(tqdm(p.imap(f, games), total=len(games)))

        return r

    def update(self, new_games, samples_per_game=4):
        """
        new_games is list of .tfrecord.zz files of new games
        """
        new_games.sort(key=lambda f: os.path.basename(f))
        for game in tqdm(new_games):
            examples = read_tfrecord_to_example_list(game)
            t = file_timestamp(game)
            choices = [(t, s)
                       for s in random.sample(examples, samples_per_game)]
            if len(self.examples) > self.max_size:
                self.examples = self.examples[samples_per_game:]
            self.examples.extend(choices)
