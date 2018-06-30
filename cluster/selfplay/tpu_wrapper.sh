#!/bin/sh
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

# Added to the player image.
# Wraps our call to cc/main

set -e

bazel-bin/cc/main \
  --model=remote \
  --inject_noise=true \
  --soft_pick=true \
  --random_symmetry=true \
  --remote_batch_size=128 \
  --parallel_games=32 \
  --batch_size=8 \
  --num_readouts=800 \
  --resign_threshold=-0.95 \
  --output_dir=gs://tmadams-sandbox/data/selfplay \
  --holdout_dir=gs://tmadams-sandbox/data/holdout \
  --sgf_dir=gs://tmadams-sandbox/sgf \
  --mode=selfplay \
  --run_forever=true
