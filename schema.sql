drop database battleship;
create database if not exists battleship;
use battleship;

drop table if exists games;
create table if not exists games (
  id integer unsigned not null auto_increment,
  user1 varchar(15),
  user2 varchar(15),
  ended boolean default 0,
  ready boolean default 0,
  current_player integer default 1,
  primary key (`id`)
) engine=InnoDB;

drop table if exists game_state;
/*create table if not exists game_state (
  game_id integer,
  user1_board varchar(1000),
  user2_board varchar(1000),
  current_player integer
) engine=InnoDB;*/



