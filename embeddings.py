import tensorflow as tf
import os
import pickle

import dual_net
import features as features_lib
import go
import sgf_wrapper
from tqdm import tqdm

# Only generate embeddings for these moves
FIRST=20
LAST=150


dual_net.flags.FLAGS([""])
sess = tf.Session()
save_file = "saved_models/000721-eagle"

features, labels = dual_net.get_inference_input()
p_out, v_out, logits, shared = dual_net.model_inference_fn(features, False)
tf.train.Saver().restore(sess, save_file)

predictions = {
    'shared': shared
}

p = go.Position()
processed = [features_lib.extract_features(p)]
res = sess.run(predictions,
               feed_dict={features: processed})

root = 'sgf/tensor-go-minigo-v10-19/sgf/eval/'

embeddings = {}
try:
  for d in os.listdir(root):
    for f in tqdm(os.listdir(os.path.join(root, d))):
      if not f.endswith('.sgf'):
        continue
      print(os.path.join(d,f))
      for idx, p in enumerate(sgf_wrapper.replay_sgf_file(os.path.join(root, d, f))):
        if idx < FIRST:
          continue
        if idx > LAST:
          break
        processed = [features_lib.extract_features(p.position)]
        res = sess.run(predictions,
                       feed_dict={features: processed})
        embeddings[ (os.path.join(root, d, f), idx)] = res['shared'][0].flatten()
except:
  raise
finally:
  pickle.dump(embeddings, open('embeddings.pickle', 'wb'))






