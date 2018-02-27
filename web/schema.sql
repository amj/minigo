
create table results (
  id integer primary key autoincrement,
  player_b text not null,
  player_w text not null,
  game_loc text not null,
  timestamp integer not null,
  b_won boolean not null
);

create table ratings (
  id integery primary key autoincrement,
  player text not null
  rating real not null,
  timestamp integer not null
);
