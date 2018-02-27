
create table results (
  game_loc text primary key,
  player_b text not null,
  player_w text not null,
  timestamp integer not null,
  b_won boolean not null
);

create table ratings (
  id integer primary key autoincrement,
  player text not null,
  rating real not null,
  timestamp integer not null
);
