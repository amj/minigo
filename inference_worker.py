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

"""
Worker process for running remote inference.
The worker wraps the inference model in an infinte loop: input features are
fetched via RPC at the top of the loop, and inference output is written back
at the bottom (again, via RPC).
"""

import sys
import time
import tensorflow as tf
from tensorflow.python.framework import dtypes
from tensorflow.contrib.proto.python.ops import decode_proto_op
from tensorflow.contrib.proto.python.ops import encode_proto_op
from absl import flags
import grpc
from proto import inference_service_pb2
from proto import inference_service_pb2_grpc
import dual_net
import features as features_lib
import go
import functools

from tensorflow.contrib.tpu.python.tpu import tpu_config
from tensorflow.contrib.tpu.python.tpu import tpu_estimator
from tensorflow.contrib.tpu.python.tpu import tpu_optimizer

flags.DEFINE_string("model", "", "Path to the TensorFlow model.")
flags.DEFINE_string("address", "localhost:50051", "Inference server address.")
flags.DEFINE_string("descriptor",
                    "proto/inference_service_py_pb2.pb.descriptor_set",
                    "Path to the InferenceService proto descriptor.")

FLAGS = flags.FLAGS


class InferenceWorkerConfig(object):
    """Configuration data for the inference worker."""

    def __init__(self, address, get_features_method, put_outputs_method,
                 batch_size, descriptor_path):
        self.address = address
        self.get_features_method = get_features_method
        self.put_outputs_method = put_outputs_method
        self.batch_size = batch_size
        self.descriptor_path = descriptor_path


def get_server_config():
    """Connects to the inference server and fetches its configuration.

    Returns:
        Server's configuration as a inference_service_pb2.GetConfigResponse
        proto.
    """
    while True:
        try:
            # Fetch the server config, used to set batch size.
            channel = grpc.insecure_channel(FLAGS.address)
            stub = inference_service_pb2_grpc.InferenceServiceStub(channel)
            return stub.GetConfig(inference_service_pb2.GetConfigRequest())
        except Exception as e:  # pylint: disable=broad-except
            print("Waiting for server")
            print(e)
            time.sleep(1)


def wrapped_model_inference_fn(config, features, params):
    """Wraps dual_net.model_inference_fn in a loop & RPC ops.

    The loop runs forever: the top of the loop issues a GetFeatures RPC to
    fetch input features, the bottom of the loop isses a PutOutputs RPC to
    write the inference output back to the server.

    Args:
        config: InferenceWorkerConfig.

    Returns:
        A tensor op that drives the model's infinite loop.
    """

    value_output_size = config.batch_size
    policy_output_size = config.batch_size * (go.N * go.N + 1)

    def loop_condition(a, unused_b):
        """Loop condition for the tf.while_loop op.

        Args:
            a: a constant 0
            unused_b: a string placeholder (to satisfy the requirement that a
                      while_loop's condition and body accept the same args as
                      the loop returns).

        Returns:
            A TensorFlow subgraph that returns true.
        """

        # TensorFlow will reject a loop unless its condition contains at least
        # one comparison. So we use (a < 1), initialize a to 0, and never
        # increment it.
        return tf.less(a[0], 1)

    def loop_body(a, unused_b):
        """Loop body for the tf.while_loop op.

        Args:
            a: a constant 0
            unused_b: a string placeholder (to satisfy the requirement that a
                      while_loop's condition and body accept the same args as
                      the loop returns).

        Returns:
            A TensorFlow subgraph.
        """

        # Request features features.
        raw_response = tf.contrib.rpc.rpc(
            address=config.address,
            method=config.get_features_method,
            request="",
            protocol="grpc",
            fail_fast=True,
            timeout_in_ms=0,
            name="get_features")

        # Decode features from a proto to a flat tensor.
        _, (batch_id, flat_features) = decode_proto_op.decode_proto(
            bytes=raw_response,
            message_type='minigo.GetFeaturesResponse',
            field_names=['batch_id', 'features'],
            output_types=[dtypes.int32, dtypes.float32],
            descriptor_source=config.descriptor_path,
            name="decode_get_features_response")

        # Reshape flat features.
        _features = tf.reshape(
            flat_features, [-1, go.N, go.N, features_lib.NEW_FEATURES_PLANES],
            name="unflatten_features")

        # Run inference.
        policy_output, value_output, _ = dual_net.model_inference_fn(
            _features, False)



        # Flatten model outputs.
        flat_policy = tf.reshape(policy_output, [-1], name="flatten_policy")
        flat_value = value_output  # value_output is already flat.

        # Encode outputs from flat tensors to a proto.
        request_tensors = encode_proto_op.encode_proto(
            message_type='minigo.PutOutputsRequest',
            field_names=['batch_id', 'policy', 'value'],
            sizes=[[1, policy_output_size, value_output_size]],
            values=[[batch_id], [flat_policy], [flat_value]],
            descriptor_source=config.descriptor_path,
            name="encode_outputs")

        # Send outputs.
        raw_response = tf.contrib.rpc.rpc(
            address=config.address,
            method=config.put_outputs_method,
            request=request_tensors,
            protocol="grpc",
            fail_fast=True,
            timeout_in_ms=0,
            name="put_outputs")

        # Decode features from a proto to a flat tensor.
        _, batch_id = decode_proto_op.decode_proto(
            bytes=raw_response,
            message_type='minigo.PutOutputsResponse',
            field_names=['batch_id'],
            output_types=[dtypes.int32],
            descriptor_source=config.descriptor_path,
            name="decode_put_outputs_response")

        return a, tf.reshape(batch_id, (1,))

    loop_vars = [features, tf.constant(0, shape=(1,), dtype=dtypes.int32)]
    loop = tf.while_loop(loop_condition, loop_body, loop_vars=loop_vars,
                         name="inference_worker_loop")

    if flags.FLAGS.use_tpu:
        return tpu_estimator.TPUEstimatorSpec(
                mode=tf.estimator.ModeKeys.PREDICT,
                predictions={'loop': loop[1]})
    else:
        return loop

def main():
    """Runs the inference worker."""

    server_config = get_server_config()
    print("server_config:\n%s" % server_config)

    if server_config.board_size != go.N:
        raise RuntimeError("Board size mismatch: server=%d, worker=%d" % (
            server_config.board_size, go.N))

    worker_config = InferenceWorkerConfig(
        address=FLAGS.address,
        get_features_method="/minigo.InferenceService/GetFeatures",
        put_outputs_method="/minigo.InferenceService/PutOutputs",
        batch_size=server_config.batch_size,
        descriptor_path=FLAGS.descriptor)

    print("building graph")
    if FLAGS.use_tpu:
        tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
            FLAGS.tpu_name, zone=None, project=None)

        config = tpu_config.RunConfig(
            cluster=tpu_cluster_resolver,
            model_dir="gs://jacksona-sandbox/models/k128-50c",
            save_checkpoints_steps=max(600, FLAGS.iterations_per_loop),
            tpu_config=tpu_config.TPUConfig(
                iterations_per_loop=FLAGS.iterations_per_loop,
                num_shards=None))
                #per_host_input_for_training=tpu_config.InputPipelineConfig.PER_HOST_V2))  # pylint: disable=line-too-long

        estimator = tpu_estimator.TPUEstimator(
            use_tpu=FLAGS.use_tpu,
            model_fn=functools.partial(wrapped_model_inference_fn, worker_config),
            config=config,
            train_batch_size=1,
            predict_batch_size=8)

        def input_fn_tpu(params):
                return tf.data.Dataset.from_tensors([tf.constant(0)])

        for item in estimator.predict(input_fn=input_fn_tpu):
            print('yay')

    else:
        tf_config = tf.ConfigProto()
        tf_config.gpu_options.allow_growth = True
        sess = tf.Session(graph=tf.Graph(), config=tf_config)
        with sess.graph.as_default():
            loop = wrapped_model_inference_fn(worker_config)
            tf.train.Saver().restore(sess, FLAGS.model)

        print("running graph")
        sess.run(loop)


if __name__ == "__main__":
    flags.FLAGS(sys.argv, known_only=True)
    main()
