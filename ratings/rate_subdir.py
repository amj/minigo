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


import sys
sys.path.insert(0, '.')

from absl import flags
from absl import app

import choix
import fnmatch
import numpy as np
import os
import re
import random
import subprocess
import math
from tqdm import tqdm
import datetime as dt
from collections import defaultdict
from ratings import math_ratings


FLAGS = flags.FLAGS

PW_REGEX = "PW\[([^]]*)\]"
PB_REGEX = "PB\[([^]]*)\]"
RESULT_REGEX = "RE\[([^]]*)\]"


def extract_pairwise(files):
    ids = defaultdict(lambda: len(ids))
    results = []
    for _file in tqdm(files):
        with open(_file) as f:
            text = f.read()
        pw = re.search(PW_REGEX, text)
        pb = re.search(PB_REGEX, text)
        result = re.search(RESULT_REGEX, text)
        if not (pw and pb and result):
            print("Player or result fields not found: ", _file)
            continue

        pw = pw.group(1)
        pb = pb.group(1)
        result = result.group(1)

        if pw == pb:
            print("Players were the same: ", _file)
            continue
        if result.lower().startswith('b'):
            results.append( (ids[pb], ids[pw]) )
        if result.lower().startswith('w'):
            results.append( (ids[pw], ids[pb]) )
    
    return ids, results


def fancyprint_ratings(ids, ratings, results=None):
    player_lookup = {v:k for k,v in ids.items()}
    HEADER = "\n{:<155s}{:>8s}{:>8s}{:>8}{:>7}-{:<8}" 
    ROW = "{:<155.153s} {:6.0f}  {:6.0f}  {:>6d}  {:>6d}-{:<6d}"

    if not results:
        for pid, (rating, sigma) in sorted(ratings.items(), 
                                           key=lambda i: i[1][0], 
                                           reverse=True):
            print("{:25s}\t{:5.1f}\t{:5.1f}".format(player_lookup[pid], rating, sigma))
        return

    wins = {pid : sum([1 for r in results if r[0] == pid]) for pid in ids.values()}
    losses = {pid : sum([1 for r in results if r[1] == pid]) for pid in ids.values()}

    
    print("\n{} games played among {} players\n".format(len(results), len(ids)))
    print(HEADER.format("Name", "Rating", "Error", "Games", "Win", "Loss"))
    max_r = max(v[0] for v in ratings.values())
    for pid, (rating, sigma) in sorted(ratings.items(), 
                                       key=lambda i: i[1][0],
                                       reverse=True):
        if rating != max_r:
            rating -= max_r 
        print(ROW.format(player_lookup[pid], rating, sigma,
            wins[pid] + losses[pid], wins[pid], losses[pid]))
    print("\n")



def main(argv):
    if len(argv) < 2:
        print("Usage: rate_subdir.py <directory of sgfs to rate>")
        sys.exit(1)
    matches = []
    for root, dirnames, filenames in os.walk(argv[1]):
        matches.extend(os.path.join(root, filename)
                for filename in fnmatch.filter(filenames, '*.sgf'))

    if not matches:
        print("No SGFs found in", argv)
        sys.exit(1)

    print("Found {} sgfs".format(len(matches)))
    ids, results = extract_pairwise(matches)
    if not results:
        for m in matches:
            print(m)
        print("No SGFs with valid results were found")
        sys.exit(1)
    rs = math_ratings.compute_ratings(results)

    fancyprint_ratings(ids, rs, results)

if __name__ == '__main__':
    app.run(main)
