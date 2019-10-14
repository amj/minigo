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


import choix
import numpy as np 
import math


def compute_ratings(data, alpha=0.0001, max_iter=800):
    """ Compute the ratings for a list of paired results.
    'data' is tuples of (winner, loser) ids.  IDs must be hashable, and no
        games with the same players are permitted.
    'alpha' & 'max_iter' are passed to choix.
    
    Returns the tuples of (id, rating, sigma)
    """
    if not data:
        raise ValueError("No pairs for rating!")
    # Get the unique list of models in the data.
    data_ids = sorted(set(np.array(data).flatten()))

    # Map data_ids to a contiguous range.
    new_id = {}
    for i, m in enumerate(data_ids):
        new_id[m] = i 

    # A function to rewrite the model_ids in our pairs
    def ilsr_data(d):
        p1, p2 = d
        p1 = new_id[p1]
        p2 = new_id[p2]
        return (p1, p2)

    pairs = list(map(ilsr_data, data))
    ilsr_param = choix.ilsr_pairwise(
        len(data_ids),
        pairs,
        alpha=alpha,
        max_iter=max_iter)

    hessian = choix.opt.PairwiseFcts(pairs, penalty=.1).hessian(ilsr_param)
    std_err = np.sqrt(np.diagonal(np.linalg.inv(hessian)))

    # "Elo" conversion
    elo_mult = 400 / math.log(10)

    # Make all ratings positive.
    min_rating = min(ilsr_param)

    ratings = {}
    for m_id, param, err in zip(data_ids, ilsr_param, std_err):
        r = (elo_mult * (param - min_rating), elo_mult * err)
        ratings[m_id] = r

    return ratings 
