import sys
sys.path.insert(0, '.')

import jinja2
import kubernetes
import yaml
import json
import os
import argh
import rl_loop
import random
import time


def launch_eval(black_num=0, white_num=0):
    if black_num <= 0 or white_num <= 0:
        print("Need real model numbers")
        return

    b = rl_loop.get_model(black_num)
    w = rl_loop.get_model(white_num)

    b_model_path = os.path.join(rl_loop.MODELS_DIR, b)
    w_model_path = os.path.join(rl_loop.MODELS_DIR, w)

    kubernetes.config.load_kube_config()
    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.BatchV1Api(
        kubernetes.client.ApiClient(configuration))

    raw_job_conf = open("cluster/evaluator/gpu-evaluator.yaml").read()
    env_job_conf = os.path.expandvars(raw_job_conf)

    t = jinja2.Template(env_job_conf)
    job_conf = yaml.load(t.render({'white': w_model_path,
                                   'black': b_model_path,
                                   'wnum': white_num,
                                   'bnum': black_num}))

    resp = api_instance.create_namespaced_job('default', body=job_conf)

    job_conf = yaml.load(t.render({'white': b_model_path,
                                   'black': w_model_path,
                                   'wnum': black_num,
                                   'bnum': white_num}))

    resp = api_instance.create_namespaced_job('default', body=job_conf)


def zoo_loop():
    desired_pairs = restore_pairs()
    last_model_queued = restore_last_model()

    kubernetes.config.load_kube_config(persist_config=True)
    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.BatchV1Api(
        kubernetes.client.ApiClient(configuration))

    try:
        while len(desired_pairs) > 0:
            last_model = rl_loop.get_latest_model()[0]
            if last_model_queued < last_model:
                print("Adding models {} to {} to be scheduled".format(
                    last_model_queued+1, last_model))
                desired_pairs += list(reversed(range(last_model_queued+1, last_model+1)))
                last_model_queued = last_model
                save_last_model(last_model)

            cleanup_finished_jobs(api_instance)
            r = api_instance.list_job_for_all_namespaces()
            if len(r.items) < 20:
                next_pair = desired_pairs.pop()
                print("Enqueuing:", next_pair)
                try:
                    make_pairs(next_pair)
                except:
                    desired_pairs.append(next_pair)
                    raise
                save_pairs(sorted(desired_pairs))
                save_last_model(last_model)

            else:
                print("{}\t{} jobs outstanding.".format(
                    time.strftime("%I:%M:%S %p"), len(r.items)))
            time.sleep(30)
    except:
        print("Unfinished pairs:")
        print(sorted(desired_pairs))
        save_pairs(sorted(desired_pairs))
        save_last_model(last_model)
        raise


def restore_pairs():
    with open('unscheduled_pairs.json') as f:
        pairs = json.loads(f.read())
    return pairs


def save_pairs(pairs):
    with open('unscheduled_pairs.json', 'w') as f:
        json.dump(pairs, f)


def save_last_model(model):
    with open('last_model.json', 'w') as f:
        json.dump(model, f)


def restore_last_model():
    with open('last_model.json') as f:
        last_model = json.loads(f.read())
    return last_model


def cleanup_finished_jobs(api):
    r = api.list_job_for_all_namespaces()
    delete_opts = kubernetes.client.V1DeleteOptions()
    for job in r.items:
        if job.status.succeeded == job.spec.completions:
            print(job.metadata.name, "finished!")
            resp = api.delete_namespaced_job(
                job.metadata.name, 'default', body=delete_opts)


def make_pairs(model_num=0):
    if model_num == 0:
        return
    for i in range(1, 10):
        launch_eval(model_num, model_num - i)
    for i in range(10, 20, 2):
        launch_eval(model_num, model_num - i)
    for i in range(20, 51, 5):
        launch_eval(model_num, model_num - i)


if __name__ == '__main__':
    argh.dispatch_command(zoo_loop)
    #for i in range(270, 280, 1):
    #    make_pairs(i)
