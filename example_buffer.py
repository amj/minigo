import tensorflow as tf
import os
import random
from tqdm import tqdm


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

def file_timestamp(filename):
    return int(os.path.basename(filename).split('-')[0])


class ExampleBuffer():
    def __init__(self, max_size=2000000):
        self.examples = []
        self.max_size = max_size

    def update(self, new_games, samples_per_game=4):
        """
        new_games is list of .tfrecord.zz files of new games
        """
        for game in tqdm(sorted(new_games, key=lambda f: os.path.basename(f))): 
            examples = read_tfrecord_to_example_list(game)
            t = file_timestamp(game)
            choices = [(t, s) for s in random.sample(examples, samples_per_game)]
            if len(self.examples) > self.max_size:
                self.examples = self.examples[samples_per_game:]
            self.examples.extend(choices)

