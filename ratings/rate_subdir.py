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


# TODO extract to common file.
def compute_ratings(data=None):
    """ Returns the dict of {model_id: (rating, sigma)}
    N.B. that `model_id` here is NOT the model number in the run

    'data' is tuples of (winner, loser) model_ids (not model numbers)
    """
    if data is None:
        with sqlite3.connect("ratings.db") as db:
            data = db.execute("select model_winner, model_loser from wins").fetchall()
    model_ids = set([d[0] for d in data]).union(set([d[1] for d in data]))

    # Map model_ids to a contiguous range.
    ordered = sorted(model_ids)
    new_id = {}
    for i, m in enumerate(ordered):
        new_id[m] = i

    # A function to rewrite the model_ids in our pairs
    def ilsr_data(d):
        p1, p2 = d
        p1 = new_id[p1]
        p2 = new_id[p2]
        return (p1, p2)

    pairs = list(map(ilsr_data, data))
    ilsr_param = choix.ilsr_pairwise(
        len(ordered),
        pairs,
        alpha=0.0001,
        max_iter=800)

    hessian = choix.opt.PairwiseFcts(pairs, penalty=.1).hessian(ilsr_param)
    std_err = np.sqrt(np.diagonal(np.linalg.inv(hessian)))

    # Elo conversion
    elo_mult = 400 / math.log(10)

    min_rating = min(ilsr_param)
    ratings = {}

    for model_id, param, err in zip(ordered, ilsr_param, std_err):
        ratings[model_id] = (elo_mult * (param - min_rating), elo_mult * err)

    return ratings


def fancyprint_ratings(ids, ratings, results=None):
    player_lookup = {v:k for k,v in ids.items()}

    if not results:
        for pid, (rating, sigma) in sorted(ratings.items(), key=lambda i: i[1][0], reverse=True):
            print("{:25s}\t{:5.1f}\t{:5.1f}".format(player_lookup[pid], rating, sigma))
        return

    wins = {pid : sum([1 for r in results if r[0] == pid]) for pid in ids.values()}
    losses = {pid : sum([1 for r in results if r[1] == pid]) for pid in ids.values()}

    
    print("\n{} games played among {} players\n".format(len(results), len(ids)))
    print("\n{:<25s}{:>8s}{:>8s}{:>8}{:^8}{:^8}".format(
        "Name", "Rating", "Error", "Games", "Wins", "Losses"))
    max_r = max(v[0] for v in sorted(ratings.values(), key=lambda v: v[0], reverse=True))
    for pid, (rating, sigma) in sorted(ratings.items(), key=lambda i: i[1][0], reverse=True):
        if rating != max_r:
            rating -= max_r 
        else:
            rating = 0
        print("{:<25.23s} {:6.0f}  {:6.0f}  {:>6d}  {:>6d}  {:<6d}".format(
            player_lookup[pid], rating, sigma, wins[pid] + losses[pid], wins[pid], losses[pid]))
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
    rs = compute_ratings(results)

    fancyprint_ratings(ids, rs, results)

if __name__ == '__main__':
    app.run(main)
