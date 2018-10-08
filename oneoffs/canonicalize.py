
import sys
sys.path.insert(0, '.')

from absl import app
from absl import flags
import sgf
import subprocess

FLAGS = flags.FLAGS

def _a(ordinal):
  """Take an int and add it to 'a'"""
  return chr(ord('a') + ordinal)

transforms = {
    0: lambda move: move,
    1: lambda move: move[0] + _a(ord('s') - ord(move[1])),
    2: lambda move: move[1]+ _a(ord('s') - ord(move[0])),
    3: lambda move: move[1]+ move[0],
    4: lambda move: _a(ord('s') - ord(move[0]))+ _a(ord('s') - ord(move[1])),
    5: lambda move: _a(ord('s') - ord(move[0]))+ move[1],
    6: lambda move: _a(ord('s') - ord(move[1]))+ move[0],
    7: lambda move: _a(ord('s') - ord(move[1]))+ _a(ord('s') - ord(move[0]))
}


def isCanonical(move, move_two):
    """ Verifies that the first two moves are 'canonical'.  i.e.,

    abcdefghi
    ........X a
    .......Xx b
    ......Xxx c
    .....Xxxx d
    ....Xxxxx e
    ......... f
    ......... g
    ......... h
    ......... i

    in one of the positions marked x.

    Additionally, if the first move is on one of the points marked X, the second move
    should be (anywhere) on the upper-left half of the board. (i.e., above the line marked y below)
    ........Y
    .......Y.
    ......Y..
    .....Y...
    ....Y....
    ...Y.....
    ..Y......
    .Y.......
    Y........
    """
    x, y = move.lower()
    #upper right
    if not (x >= 'j' and y <= 'j'):
        return False

    # the correct part of the upper right?
    flip = chr(ord('a') + ord('s') - ord(y))
    if flip > x:
        return False

    #if it's a symmetrical position, check move 2
    if x == chr(ord('a') + ord('s') - ord(y)):
        x2, y2 = move_two
        flip = chr(ord('a') + ord('s') - ord(y2))
        if flip < x2:
            return False
    return True


def find_transform(moves):
    for k,tr in transforms.items():
        if isCanonical( tr(moves[0]), tr(moves[1]) ):
            return k
    raise ValueError("No transform canonicalizes %s" % moves)


def get_first_two_moves(sgftext):
    collection = sgf.parse(sgftext)
    tree = collection[0]
    if not ('B' in tree.nodes[1].properties and 'W' in tree.nodes[2].properties):
        raise ValueError( "invalid game %s" % filename)

    return tree.nodes[1].properties['B'][0], tree.nodes[2].properties['W'][0]


def main(argv):
    for filename in argv[1:]:
        with open(argv[1], 'rb', 0) as _in:
            strip = subprocess.run(
                ['sgfstrip', 'C'], stdin=_in, stdout=subprocess.PIPE)
        sgftext = str(strip.stdout, encoding='utf-8')
        moves = get_first_two_moves(sgftext)
        tr = find_transform(moves)
        cmd = ["sgftf", "-tra%d" % tr]
        subprocess.run(cmd, input=bytes(sgftext, encoding='utf-8'),
                       stdout=sys.stdout, stderr=sys.stderr)


import coords
k2s = lambda move: coords.to_sgf(coords.from_kgs(move))

assert isCanonical(k2s('R16'), k2s('D16'))  # one 3-4 is ok
assert not isCanonical(k2s('Q17'), k2s('D16')) # the 4-3 is not
assert not isCanonical(k2s('Q4'), k2s('D16')) # the bottom right is out
assert not isCanonical(k2s('D4'), k2s('D16')) # the lower right is out
assert isCanonical(k2s('Q16'), k2s('R17')) # Invading 3-3 is fine
assert isCanonical(k2s('Q16'), k2s('O17')) # approaching one way is fine
assert not isCanonical(k2s('Q16'), k2s('R14')) # approaching the other is not
assert isCanonical(k2s('K10'), k2s('O17')) # K10 is fine
assert not isCanonical(k2s('K10'), k2s('L10')) # ...but move 2 should be upper right
assert not isCanonical(k2s('K10'), k2s('K9'))  # ...but move 2 should be upper right
assert isCanonical(k2s('K10'), k2s('J10'))  # ...but move 2 should be upper right


if __name__ == '__main__':
  app.run(main)




