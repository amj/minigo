# Copyright 2019 Google LLC
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

# Lint as: python3
"""Look for estimator-like working dirs and launch tensorboard;

Scrapes a directory with many subdirectories of estimator-like results and calls tensorboard with a formatted --logdir string for all found subdirectories that have tensorboard logs in them.

E.g.

Given 'results', and results contains
  results/foo/work_dir
  results/bar/work_dir

It will run:
  tensorboard --logdir=foo:results/foo/work_dir,bar:results/bar/work_dir
"""

import os
import subprocess

from absl import app
from absl import flags

flags.DEFINE_integer("port", 5001, "Port to listen on.")
flags.DEFINE_string("results_dir", "", "Directory to scan for tb log-like subdirs")

FLAGS = flags.FLAGS

def build_tb_flags(results_dir, port):
  dirs = [d for d in os.listdir(results_dir)
          if os.path.isdir(os.path.join(results_dir, d)) and
          os.path.exists(os.path.join(results_dir, d, 'work_dir'))]

  tb_dirs = ["{}:{}".format(d, os.path.join(results_dir, d, 'work_dir')) for d in dirs]
  tb_dirs = ",".join(tb_dirs)
  print(tb_dirs)

  return ["--logdir={}".format(tb_dirs), "--port={}".format(port)]


def main(argv):
  tb_flags = build_tb_flags(FLAGS.results_dir, FLAGS.port)
  process = subprocess.call(
      ['tensorboard'] + tb_flags)

if __name__ == '__main__':
  app.run(main)
