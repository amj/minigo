import sys
sys.path.insert(0, '.')

import jinja2
import kubernetes
import yaml
import os
import argh
import rl_loop


def launch_eval(black_num=0, white_num=0):
    if black_num == 0 or white_num == 0:
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
    #argh.dispatch_command(make_pairs)
    for i in range(209, 240):
        make_pairs(i)
