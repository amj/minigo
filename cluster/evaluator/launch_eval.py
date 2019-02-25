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

import sys
sys.path.insert(0, '.')

import json
import os
import re
import time
from collections import Counter

import fire
import random
from absl import flags
import kubernetes
import yaml

from rl_loop import fsdb
from ratings import ratings

MAX_TASKS = 300  # Keep < 500, or k8s may not track completions accurately.
MIN_TASKS = 100


def launch_eval_job(m1_path, m2_path, job_name, bucket_name, completions=5):
    """Launches an evaluator job.
    m1_path, m2_path: full gs:// paths to the .pb files to match up
    job_name: string, appended to the container, used to differentiate the job
    names (e.g. 'minigo-cc-evaluator-v5-123-v7-456')
    bucket_name: Where to write the sgfs, passed into the job as $BUCKET_NAME
    completions: the number of completions desired
    """
    if not all([m1_path, m2_path, job_name, bucket_name]):
        print("Provide all of m1_path, m2_path, job_name, and bucket_name "
              "params")
        return

    def isGsPath(path):
        return path.startswith('gs://')

    assert isGsPath(m1_path), 'm1_path: ' + m1_path + ' must start gs://'
    assert isGsPath(m2_path), 'm2_path: ' + m2_path + ' must start gs://'
    assert not isGsPath(bucket_name), 'bucket_name must not be gs:// path'

    api_instance = get_api()

    raw_job_conf = open("cluster/evaluator/cc-evaluator.yaml").read()

    os.environ['BUCKET_NAME'] = bucket_name

    os.environ['MODEL_BLACK'] = m1_path
    os.environ['MODEL_WHITE'] = m2_path
    os.environ['JOBNAME'] = job_name + '-bw'
    env_job_conf = os.path.expandvars(raw_job_conf)

    job_conf = yaml.load(env_job_conf)
    job_conf['spec']['completions'] = completions

    resp_bw = api_instance.create_namespaced_job('default', body=job_conf)

    os.environ['MODEL_WHITE'] = m1_path
    os.environ['MODEL_BLACK'] = m2_path
    os.environ['JOBNAME'] = job_name + '-wb'
    env_job_conf = os.path.expandvars(raw_job_conf)
    job_conf = yaml.load(env_job_conf)
    job_conf['spec']['completions'] = completions

    resp_wb = api_instance.create_namespaced_job('default', body=job_conf)
    return job_conf, resp_bw, resp_wb


def same_run_eval(black_num=0, white_num=0):
    """Shorthand to spawn a job matching up two models from the same run,
    identified by their model number """
    if black_num <= 0 or white_num <= 0:
        print("Need real model numbers")
        return

    b = fsdb.get_model(black_num)
    w = fsdb.get_model(white_num)

    b_model_path = os.path.join(fsdb.models_dir(), b)
    w_model_path = os.path.join(fsdb.models_dir(), w)

    return launch_eval_job(b_model_path + ".pb",
                           w_model_path + ".pb",
                           "{}-{}".format(black_num, white_num),
                           flags.FLAGS.bucket_name)


def cross_run_eval(run_a, model_a, run_b, model_b):
    """Shorthand to spawn a job matching up two models from the different run,
    identified by their bucket and model number """

    run_a = run_a.replace('-19x19', '')
    run_b = run_b.replace('-19x19', '')
    assert len(run_a) in (2,3) and len(run_b) in (2,3), (run_a, run_b)
    model_re = re.compile(r'^[0-9]{6}-[a-z-]*$')
    assert model_re.match(model_a), model_a
    assert model_re.match(model_b), model_b

    num_a = int(model_a.split('-')[0])
    num_b = int(model_b.split('-')[0])
    assert 0 <= num_a <= 1100, num_a
    assert 0 <= num_b <= 1100, num_b

    PROJECT = os.environ.get("PROJECT")
    bucket_a = "gs://{}-minigo-{}-19".format(PROJECT, run_a)
    bucket_b = "gs://{}-minigo-{}-19".format(PROJECT, run_b)

    path_a = os.path.join(bucket_a, 'models', model_a + ".pb")
    path_b = os.path.join(bucket_b, 'models', model_b + ".pb")

    tag = '{}-{}-vs-{}-{}'.format(run_a, num_a, run_b, num_b)

    cross_eval_bucket = PROJECT + '-minigo-cross-evals'
    return launch_eval_job(path_a, path_b, tag, cross_eval_bucket, 5)


def _append_pairs(new_pairs, dry_run):
    desired_pairs = restore_pairs() or []
    desired_pairs += new_pairs
    print("Adding {} new pairs, queue has {} pairs".format(len(new_pairs), len(desired_pairs)))
    if not dry_run:
        save_pairs(desired_pairs)


def add_uncertain_pairs(dry_run=False):
    new_pairs = ratings.suggest_pairs()
    _append_pairs(new_pairs, dry_run)



def get_cross_eval_pairs():
    all_models = read_cross_run_models()
    print(len(all_models), "cross eval models")

    # key in ratings.db
    model_ids = {m[1]: ratings.model_id(m[1]) for m in all_models}
    assert len(model_ids) == len(all_models), "Duplicate model name!"
    assert len(model_ids) >= len(set(model_ids.values())), "Duplicate row!"

    raw_scores = ratings.compute_ratings()
    rs = {ratings.model_name_for(k): v for k, v in raw_scores.items()}
    ranks = {k: i for i, (r,k) in enumerate(sorted((r,k) for k, r in rs.items()))}
    print (len(rs), "ratings")

    game_counts = Counter(ratings.wins_subset(fsdb.models_dir()))
    print ("Found", sum(game_counts.values()), "games")

    model_game_counts = Counter()
    for (winner, loser), count in game_counts.items():
        model_game_counts[winner] += count
        model_game_counts[loser] += count

    existing_pairs, previous_pairs = restore_pairs()
    max_uncertainty = float(max([r[1] for r in rs.values()]))

    import pdb
    pdb.set_trace()

    # priority is roughly related to expected gain of information
    pairs = []
    for run_a, model_a in all_models:
        for run_b, model_b in all_models:
            if (run_a, model_a) >= (run_b, model_b):
                continue

            # Potentially relax this a portion of the time.
            if run_a == run_b:
                continue

            pair = [run_a, model_a, run_b, model_b]
            # If already being processed, will cause kubernetes error.
            if pair in previous_pairs:
                continue

            # if not present use model_num as rating which helps sparse rating.
            r_a = rs.get(model_a, [3 * int(model_a.split('-')[0]), 0])
            r_b = rs.get(model_b, [3 * int(model_b.split('-')[0]), 0])

            model_id_a = model_ids[model_a]
            model_id_b = model_ids[model_b]

            # count of head to head encounters.
            games = (game_counts[(model_id_a, model_id_b)] +
                     game_counts[(model_id_b, model_id_a)])

            # count of games played by each model.
            model_a_games = model_game_counts[model_id_a]
            model_b_games = model_game_counts[model_id_b]


            # Controls how much to explore unique pairs verus equal strength.
            games_power = 0.7
            equality_const = 0.8
            uncertainty_const = 1200
            high_ratings_const = 0.02

            # priority based on being highly ranked
            # Higher = better
            rank_num = min(ranks.get(model_a, 0), ranks.get(model_b, 0))

            if (rank_num + 25) < len(rs):
                continue 

            rank_adjustment = (1 + rank_num / len(rs)) ** 2 / 4

            # priority based on model variances
            avg_u = (r_a[1] + r_b[1]) / 2.0
            uncertainty_priority = avg_u / max_uncertainty

            # priority based on information gained by playing this pairing
            win_prob = abs(1 / (1 + 10 ** (-(r_a[0] - r_b[0])/400)))
            game_quality = win_prob * (1 - win_prob) + rank_adjustment

            # priority based on playing a game with this model
            model_priority = (1 / (1 + model_a_games) ** games_power +
                              1 / (1 + model_b_games) ** games_power)

            priority = game_quality + model_priority + uncertainty_priority

#            print("{}:{} vs {}:{}"
#                    "\t{:0.2f} {:0.2f} {:0.2f} = {:0.2f}".format(
#                        run_a, model_a, run_b, model_b,
#                        game_quality, model_priority, uncertainty_priority, priority))

            pairs.append((
                [rank_adjustment * priority,
                 rank_adjustment, win_prob, uncertainty_priority,
                 games, model_a_games, model_b_games],
                pair))

    pairs.sort(reverse=True)
    models_queued = set()

    new_pairs = []
    for priority, pair in pairs:
        if len(new_pairs) >= 8:
            break

        if pair in existing_pairs:
            continue

        if pair[1] in models_queued or pair[3] in models_queued:
            continue

        new_pairs.append(pair)
        models_queued.add(pair[1])
        models_queued.add(pair[3])

        print ("Priority: {:.3f}, rank adj: {:.2f}, win_prob: {:.2f}, var: {:.1f}, games: {}, {}, {}, pair: {}/{}, {}/{}".format(
            *(priority + pair)))

    existing_pairs += new_pairs
    print("Adding {} new pairs, queue has {} pairs".format(
        len(new_pairs), len(existing_pairs)))
    print()
    save_pairs((existing_pairs, previous_pairs))



def add_top_pairs(dry_run=False):
    """ Pairs up the top twenty models against each other.
    #1 plays 2,3,4,5, #2 plays 3,4,5,6 etc. for a total of 15*4 matches.
    """
    top = ratings.top_n(10)
    new_pairs = []
    for idx, t in enumerate(top[:5]):
        new_pairs += [[t[0], o[0]] for o in top[idx+1:idx+5]]
    print(new_pairs)
    _append_pairs(new_pairs, dry_run)


def cross_run_eval_matchmaker_loop(sgf_dir, max_jobs=60):
    """Manages creating and cleaning up cross bucket evaluation jobs.

    sgf_dir -- the directory where sgf eval games should be used for computing
      ratings.
    max_jobs -- the maximum number of concurrent jobs.  jobs * completions * 2
      should be around 200 to keep kubernetes from losing track of completions
    """
    desired_pairs, existing_pairs = restore_pairs()

    if sgf_dir:
        sgf_dir = os.path.abspath(sgf_dir)

    api_instance = get_api()
    toggle = True
    try:
        while True:
            cleanup(api_instance)
            random.shuffle(desired_pairs)
            r = api_instance.list_job_for_all_namespaces()

            if len(r.items) >= max_jobs:
                print("{}\t{} jobs outstanding. ({} in the queue)".format(
                      time.strftime("%I:%M:%S %p"),
                      len(r.items), len(desired_pairs)))
                time.sleep(30)

            if r.items:
                tasks = sum([item.spec.completions for item in r.items])
            else:
                tasks = 0
            if tasks < MAX_TASKS:
                if len(desired_pairs) == 0:
                    if sgf_dir:
                        if tasks > MIN_TASKS:
                            time.sleep(30)
                            continue
                        print("Out of pairs!  Syncing new eval games...")
                        ratings.sync(sgf_dir)
                        print("Updating ratings and getting suggestions...")

                        get_cross_eval_pairs()
                        desired_pairs, existing_pairs = restore_pairs()
                        print("Got {} new pairs".format(len(desired_pairs)))
                    else:
                        print("Out of pairs!  Sleeping")
                        time.sleep(300)
                        continue

                next_pair = desired_pairs.pop()
                print("Queue", len(desired_pairs), "items", len(existing_pairs), "previous")
                existing_pairs.append(next_pair)
                print("Enqueuing:", next_pair)

                cross_run_eval(*next_pair)
                save_pairs((desired_pairs, existing_pairs[-80:]))
                time.sleep(6)

            else:
                print("{}\t {} finished / {} requested. "
                      "({} jobs, {} pairs to be scheduled)".format(
                      time.strftime("%I:%M:%S %p"),
                      sum([i.status.succeeded or 0 for i in r.items]),
                      tasks, len(r.items), len(desired_pairs)))
                time.sleep(30)
    except:
        print("Finished pairs:", len(existing_pairs))
        print("Unfinished pairs:")
        print(desired_pairs)
        save_pairs((desired_pairs, existing_pairs))
        raise

def read_json(filename):
    with open(filename) as f:
        return json.loads(f.read())

def write_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def restore_pairs():
    return read_json('pairlist.json')

def save_pairs(pairs):
    write_json('pairlist.json', pairs)

def restore_last_model():
    return read_json('last_model.json')

def save_last_model(model):
    write_json('last_model.json', model)

def read_cross_run_models():
    return read_json('oneoffs/cross_eval_models.json')

def get_api():
    kubernetes.config.load_kube_config(persist_config=True)
    configuration = kubernetes.client.Configuration()
    return kubernetes.client.BatchV1Api(
        kubernetes.client.ApiClient(configuration))


def cleanup(api_instance=None):
    """ Remove completed jobs from the cluster """
    api = api_instance or get_api()
    r = api.list_job_for_all_namespaces()
    delete_opts = kubernetes.client.V1DeleteOptions()
    for job in r.items:
        if job.status.succeeded == job.spec.completions:
            print(job.metadata.name, "finished!")
            api.delete_namespaced_job(
                job.metadata.name, 'default', body=delete_opts)


def make_pairs_for_model(model_num=0):
    """ Create a list of pairs of model nums; play every model nearby, then
    every other model after that, then every fifth, etc.

    Returns a list like [[N, N-1], [N, N-2], ... , [N, N-12], ... , [N, N-50]]
    """
    if model_num == 0:
        return
    pairs = []
    pairs += [[model_num, model_num - i]
              for i in range(1, 5) if model_num - i > 0]
    pairs += [[model_num, model_num - i]
              for i in range(5, 71, 10) if model_num - i > 0]
    return pairs


if __name__ == '__main__':
    remaining_argv = flags.FLAGS(sys.argv, known_only=True)
    fire.Fire({
        'cross_run_eval_matchmaker_loop': cross_run_eval_matchmaker_loop,
        'same_run_eval': same_run_eval,
        'cross_run_eval': cross_run_eval,
        'cleanup': cleanup,
        'get_cross_eval_pairs': get_cross_eval_pairs,
        'add_top_pairs': add_top_pairs,
        'launch_eval_job': launch_eval_job,
    }, remaining_argv[1:])
