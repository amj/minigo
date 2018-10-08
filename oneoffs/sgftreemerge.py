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
"""Merge sgf records of a common player into subtrees.

Take a list of files of sgfs all played with a common player, group them into 
"""


from absl import app
from absl import flags

#N.B. this uses sgfmill's sgf library
from sgfmill import sgf
import collections

FLAGS = flags.FLAGS

PROPS = ['RE', 'PB', 'PW']

def decorate_tail(tree, filename):
    """Given a single-line game, move the filename and metadata annotations
    (players, result) into the final node's comment.  `tree` is modified in place.
      """
    tail = tree.get_main_sequence()[-1]
    tail.add_comment_text(filename)
    for p in PROPS:
      tail.add_comment_text("%s: %s" % (p, tree.root.get(p).strip()))

def merge_tree(source, target):
    """
    Merge `source` into `target`.
    Neither should have an empty setup node.
    `source` should have no variations, only a single main line.

    #1. Find the node in 'target' where source and target diverge.
      set `target_parent` to the move above
      `source_n` is the move that differs
    #2. Determine if any of PW/PB/RE differ from source and target.
    #3. Set the metadata on the 
    """
    if (source.get_player_name('b') != target.get_player_name('b')) and (source.get_player_name('w') != target.get_player_name('w')):
        raise ValueError("Source and target do not share at least one common player!")
    found = True
    source_n = source.get_main_sequence()[0]
    target_n = target.get_main_sequence()[0]
    while found:
      if len(source_n) > 1:
        raise ValueError("Branched tree given as source for merge!")
      found = False
      if not target_n:
        print("Games are identical!")
        return
      for child in target_n:
        if child.get_move() == source_n[0].get_move():
          source_n = source_n[0]
          target_n = child
          found = True
          break

    # Update game-info properties at point of divergence.
    for prop in PROPS:
        try:
            if source_n.owner.root.get(prop) != target_n.find_property(prop):
                target_re_node = target_n.find(prop)
                # copy this to the targets kids
                for kid in target_re_node:
                    kid.set(prop, target_re_node.get(prop))
                #unset it from the target
                target_re_node.unset(prop)
        except KeyError:
            #this happens if the branch point is already the same
            pass
        #set the (different) value on the source's kid
        source_n[0].set(prop, source_n.find_property(prop))

    # TODO: annotate divergence/statistics here.  Might need filename?
    reparent(source_n[0], target_n)


def reparent(node, new_parent, index=None):
    # sgfmill.sgfnode.reparent checks for same-tree ownership so...
    node.owner = new_parent.owner # duckpunch it in :)
    node.reparent(new_parent)

def count_wins(node, my_color='B'):
    unexplored = [node]
    ct = 0
    wins = 0
    while unexplored:
        n = unexplored.pop()
        if n:
            unexplored.extend(n._children)
        else:
            ct+= 1
            if n.find_property('RE').startswith(my_color):
                wins += 1
    return wins, ct

def count_leaves(node):
    while len(node) == 1: #keep the stack manageable
        node = node[0]
    if not node:
        return 1 
    return sum((count_leaves(kid) for kid in node))

def annotate_wins(node, my_color='B'):
  unexplored = [node]
  while unexplored:
    n = unexplored.pop()
    if n:
      unexplored.extend(n._children)
    if len(n) > 1:
      for kid in n:
        kid.add_comment_text('Wins: %d / %d' % count_wins(kid, my_color=my_color))


def main(argv):
  print("Parsing games...", end="")
  gs = dict([(f, sgf.Sgf_game.from_string(open(f).read())) for f in argv[1:]])
  print(" done.")
  players = collections.Counter([g.get_player_name('w') for g in gs.values()])
  players.update([g.get_player_name('b') for g in gs.values()])
  my_player = players.most_common(1)[0][0]
  print("Compiling records for", my_player)
  my_b_games = [(f,g) for f,g in gs.items() if g.get_player_name('b') == my_player]
  my_w_games = [(f,g) for f,g in gs.items() if g.get_player_name('w') == my_player]
  for f,g in my_b_games:
      decorate_tail(g, f)
      merge_tree(g, my_b_games[0][1])
  for f,g in my_w_games:
      decorate_tail(g, f)
      merge_tree(g, my_w_games[0][1])

  print(count_wins(my_b_games[0][1].root))
  print(count_wins(my_w_games[0][1].root))
  annotate_wins(my_b_games[0][1].root, my_color='B')
  annotate_wins(my_w_games[0][1].root, my_color='W')

  with open(my_player + '_b.sgf', 'w') as out:
    out.write(str(my_b_games[0][1].serialise(), encoding='utf-8'))

  with open(my_player + '_w.sgf', 'w') as out:
    out.write(str(my_w_games[0][1].serialise(), encoding='utf-8'))

if __name__ == '__main__':
  app.run(main)
