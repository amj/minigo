competition_type = "allplayall"
description = """ MiniGo Top models vs Leela-Zero, time equality, proper PUCT (1.25)"""
record_games = True
stderr_to_log = True

board_size = 19
komi = 7.5

players = {
  "mg_939-heron": Player(
        "./leelaz -g --noponder -w 000939-heron_converted.txt -t 1 "
        "--lagbuffer 0 --timemanage off -r 20",
        startup_gtp_commands=["time_settings 0 {} 1".format(10)],
        ),
  "leela-201": Player(
        "./leelaz -g --noponder -w best-network -t 1 -r 20 "
        "--lagbuffer 10 --timemanage off",
        startup_gtp_commands=["time_settings 0 {} 1".format(10)],
        )
}

rounds = 1
competitors= ["mg_939-heron", "leela-201"]
