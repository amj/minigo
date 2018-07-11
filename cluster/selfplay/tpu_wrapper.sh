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
  --remote_inference=true \
  --model=gs://tensor-go-minigo-v7-19/models/000485-onslaught \
  --inject_noise=true \
  --soft_pick=true \
  --random_symmetry=true \
  --virtual_losses=8 \
  --games_per_inference=16 \
  --parallel_games=32 \
  --num_readouts=800 \
  --resign_threshold=-0.95 \
  --output_dir=gs://tmadams-sandbox/data/selfplay \
  --holdout_dir=gs://tmadams-sandbox/data/holdout \
  --sgf_dir=gs://tmadams-sandbox/sgf \
  --mode=selfplay \
  --run_forever=true
