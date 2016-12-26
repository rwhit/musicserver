-- setup schema

-- podcasts
create table podcast_feeds (
  id SERIAL,
  label varchar(128) not null,
  image_url varchar(256),
  url varchar(256) not null,
  rank int not null,
  last_retrieved timestamp with time zone,
  last_listened timestamp with time zone,

  primary key(id),
  unique(rank) deferrable INITIALLY DEFERRED 
);

comment on column podcast_feeds.rank is 'primary user-specified sort order - lowest at top';

create table podcast_items (
  id SERIAL,
  feed_id int not null,
  url varchar(256) not null,
  duration_secs int,
  position_secs int,
  last_listened timestamp with time zone,
  status int,

  primary key(id),
  foreign key (feed_id) references podcast_feeds(id) on delete cascade
);

comment on column podcast_items.status is 'bitflag - 1 played';

-- radio stations
create table radio_stations (
  id SERIAL,
  label varchar(128) not null,
  image_url varchar(256),
  url varchar(256) not null,
  rank int not null,
  last_listened timestamp with time zone,

  primary key(id),
  unique(rank)
);

-- added for npr one, but general place to persist stuff
create table app_state (
  namespace varchar(128) not null,
  key varchar(128) not null,
  value json not null,

  primary key(namespace, key)
);

  
