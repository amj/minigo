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

"""Wrapper scripts to ensure that main.py commands are called correctly."""
import argh
import argparse
import cloud_logging
import logging
import os
import main
import shipname
from utils import timer
from tensorflow import gfile

# Pull in environment variables. Run `source ./cluster/common` to set these.
BUCKET_NAME = os.environ['BUCKET_NAME']

BASE_DIR = "gs://{}".format(BUCKET_NAME)
MODELS_DIR = os.path.join(BASE_DIR, 'models')
SELFPLAY_DIR = os.path.join(BASE_DIR, 'data/selfplay')
HOLDOUT_DIR = os.path.join(BASE_DIR, 'data/holdout')
SGF_DIR = os.path.join(BASE_DIR, 'sgf')
TRAINING_CHUNK_DIR = os.path.join(BASE_DIR, 'data', 'training_chunks')


def print_flags():
    flags = {
        'BUCKET_NAME': BUCKET_NAME,
        'BASE_DIR': BASE_DIR,
        'MODELS_DIR': MODELS_DIR,
        'SELFPLAY_DIR': SELFPLAY_DIR,
        'HOLDOUT_DIR': HOLDOUT_DIR,
        'SGF_DIR': SGF_DIR,
        'TRAINING_CHUNK_DIR': TRAINING_CHUNK_DIR,
    }
    print("Computed variables are:")
    print('\n'.join('--{}={}'.format(flag, value)
                    for flag, value in flags.items()))


def all_models():
    """Returning all model numbers and name

    Returns: [(17, 000017-modelname), (13, 000013-modelname), etc]
    """
    all_models = gfile.Glob(os.path.join(MODELS_DIR, '*.meta'))
    model_filenames = [os.path.basename(m) for m in all_models]
    return [(shipname.detect_model_num(m), shipname.detect_model_name(m))
            for m in model_filenames]


def get_model(num):
    """Finds the model name for a given number"""
    models_by_num = dict(all_models())
    return models_by_num.get(num, None)


def get_latest_model():
    """Get the most recent model.

    Returns: (17, 000017-modelname)
    """
    model_numbers_names = all_models()
    latest_model = sorted(model_numbers_names, reverse=True)[0]
    return latest_model


def game_counts(n_back=20):
    """Prints statistics for the most recent n_back models"""
    all_models = gfile.Glob(os.path.join(MODELS_DIR, '*.meta'))
    model_filenames = sorted([os.path.basename(m).split('.')[0]
                              for m in all_models], reverse=True)
    for m in model_filenames[:n_back]:
        games = gfile.Glob(os.path.join(SELFPLAY_DIR, m, '*.zz'))
        print(m, len(games))


def bootstrap():
    bootstrap_name = shipname.generate(0)
    bootstrap_model_path = os.path.join(MODELS_DIR, bootstrap_name)
    print("Bootstrapping model at {}".format(bootstrap_model_path))
    main.bootstrap(bootstrap_model_path)


def selfplay(readouts=1600, verbose=2, resign_threshold=0.99):
    _, model_name = get_latest_model()
    print("Playing a game with model {}".format(model_name))
    model_save_file = os.path.join(MODELS_DIR, model_name)
    game_output_dir = os.path.join(SELFPLAY_DIR, model_name)
    game_holdout_dir = os.path.join(HOLDOUT_DIR, model_name)
    sgf_dir = os.path.join(SGF_DIR, model_name)
    main.selfplay(
        load_file=model_save_file,
        output_dir=game_output_dir,
        holdout_dir=game_holdout_dir,
        output_sgf=sgf_dir,
        readouts=readouts,
        verbose=verbose,
    )


def gather():
    print("Gathering game output...")
    main.gather(input_directory=SELFPLAY_DIR,
                output_directory=TRAINING_CHUNK_DIR)


def train(logdir=None, start_from=-1, models_dir=MODELS_DIR):
    latest_model_num, latest_model_name = get_latest_model()

    model_num, model_name = start_from, get_model(start_from)
    if model_name is None:
        print("Model", start_from, "not found.  Starting from latest...")
        model_name = latest_model_name

    print("Training on gathered game data, initializing from {}".format(model_name))
    print("Saving to:", models_dir)

    while model_num <= latest_model_num:
        new_model_name = shipname.generate(model_num + 1)
        print("New model will be {}".format(new_model_name))
        load_file = os.path.join(models_dir, model_name)
        save_file = os.path.join(models_dir, new_model_name)
        main.train(TRAINING_CHUNK_DIR, save_file=save_file, load_file=load_file,
                   data_up_to=model_num, logdir=logdir)
        model_num += 1
        load_file = save_file


parser = argparse.ArgumentParser()

argh.add_commands(parser, [train, selfplay, gather, bootstrap, game_counts])

if __name__ == '__main__':
    print_flags()
    cloud_logging.configure()
    argh.dispatch(parser)
