"""
Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
""" 

import choix
import numpy as np
import sqlite3
import os, os.path
import re
import fsdb


EVAL_REGEX = "(\d*)-minigo-cc-evaluator-"
MODEL_REGEX = "(\d*)-(.*)"
PW_REGEX = "PW\[(.*?)\]"
PB_REGEX = "PB\[(.*?)\]"
RESULT_REGEX = "RE\[(.*?)\]"

def maybe_insert_model(db, bucket, name, num): 
    with db:
        db.execute( """insert or ignore into models(model_name, model_num, bucket, num_games, num_wins, black_games, black_wins, white_games, white_wins) 
                                          values(?, ?, ?, 0, 0, 0, 0, 0, 0)""",
                                          [name, num, bucket])

def rowid_for(db, bucket,name):
    try:
        return db.execute("select id from models where bucket = ? and model_name = ?", [bucket, name]).fetchone()[0]
    except:
        print("No row found for bucket: {} name: {}".format(bucket, name))
        return None


def import_files(files):
    db = sqlite3.connect("ratings.db")
    for _file in files:
        match = re.match(EVAL_REGEX, os.path.basename(_file))
        if not match:
            print("Bad file: ", _file)
            continue
        timestamp = match.groups(1)[0]
        with open(_file) as f:
            text = f.read()
        pw = re.search(PW_REGEX, text)
        pb = re.search(PB_REGEX, text)
        result = re.search(RESULT_REGEX, text)
        if not pw or not pb or not result:
            print("Fields not found: ", _file)

        pw = pw.group(1)
        pb = pb.group(1)
        result = result.group(1)

        m_num_w = re.match(MODEL_REGEX, pw).group(1)
        m_num_b = re.match(MODEL_REGEX, pb).group(1)

        try:
            # create models or ignore.
            maybe_insert_model(db, fsdb.models_dir(), pb, m_num_b)
            maybe_insert_model(db, fsdb.models_dir(), pw, m_num_w)

            b_id = rowid_for(db, fsdb.models_dir(), pb)
            w_id = rowid_for(db, fsdb.models_dir(), pw)

            # insert into games or bail
            game_id = None
            try: 
                with db:
                    c = db.cursor()
                    c.execute(
                    """ insert into games(timestamp, filename, b_id, w_id, black_won, result)
                                    values(?, ?, ?, ?, ?, ?)
                    """, [timestamp, _file, b_id, w_id, result.lower().startswith('b'), result])
                    game_id = c.lastrowid
            except sqlite3.IntegrityError:
                #print("Duplicate game: {}".format(_file))
                continue

            if game_id is None:
                print("Somehow, game_id was None")

            # update wins/game counts on model, and wins table.
            with db:
                c = db.cursor()
                c.execute("update models set num_games = num_games + 1 where id in (?, ?)", [b_id, w_id])
                if result.lower().startswith('b'):
                    c.execute("update models set black_games = black_games + 1, black_wins = black_wins + 1 where id = ?", (b_id,))
                    c.execute("update models set white_games = white_games + 1 where id = ?", (w_id,))
                    c.execute("insert into wins(game_id, model_winner, model_loser) values(?, ?, ?)", 
                                [game_id, b_id, w_id])
                elif result.lower().startswith('w'):
                    c.execute("update models set black_games = black_games + 1 where id = ?", (b_id,))
                    c.execute("update models set white_games = white_games + 1, white_wins = white_wins + 1 where id = ?", (w_id,))
                    c.execute("insert into wins(game_id, model_winner, model_loser) values(?, ?, ?)", 
                                [game_id, w_id, b_id])
                db.commit() 

        except sqlite3.OperationalError:
            print("Bailed!")
            db.rollback()
            db.commit()
            raise
        except:
            print("Bailed!")
            db.rollback()
            db.commit()
            raise


def main():
    root = "/Users/andrew/work/minigo2/sgf/eval/" 
    dirs = os.listdir(root)
    print(dirs)
    for d in dirs:
        if os.path.isdir(os.path.join(root,d)):
            fs = [os.path.join(root, d, f) for f in os.listdir(os.path.join(root, d))]
            print("Importing from {}".format(d))
            import_files(fs)

def rate():
    db = sqlite3.connect("ratings.db")
    with db:
        c = db.cursor()
        c.execute("select model_winner, model_loser from wins")
        data = c.fetchall()


if __name__ == '__main__':
    main()
