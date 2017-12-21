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

-- specifically for podcasts, but general purpose
create table cache_status (
  state int,
  name text,

  primary key(state)
);
insert into cache_status (state, name)
  values
    (0, 'init'),
    (1, 'downloading'),
    (2, 'complete'),
    (3, 'error'),
    (4, 'expired') -- removed from disk but (possibly) still in feed
;
create table file_cache (
  id SERIAL,
  url text not null,
  path text,
  created timestamp with time zone not null default now(),
  last_read timestamp with time zone,
  size int,
  state int not null default 0,
  attempts int not null default 0,
  -- how many download attempts?
  source_group text not null, -- e.g. rss feed, to aid w/expiration
  present_at_source boolean not null default 't',

  -- add checks when state == 2 - path & size cannot be null
  primary key(id),
  unique(url),
  unique(path),

  foreign key (state) references cache_status (state)
);

-- album support
create table artist (
  id SERIAL,
  name text,

  primary key (id),
  unique(name)
);

create table playlist (
  id SERIAL,
  name text not null,
  type text not null check (type in ('manual', 'album')),
  duration_secs integer,
  duration_is_estimate boolean,

  primary key (id),
  unique(name)
);

-- should rename something like "collection"?
create table album (
  id SERIAL,
  title text not null,
  artist_id integer not null,
  playlist_id integer,
  path text not null,

  primary key (id),
  unique(title, artist_id),
  unique(path),

  foreign key (artist_id) references artist(id),
  foreign key (playlist_id) references playlist(id)
);
create index idx_albums_artist on album(artist_id);

-- to populate (almost - and doesn't handle artist_id):
-- ( echo "insert into albums(title, artist, path) values"; ls /data/dobby/ripped-cds/ |
--     sed 's/ - /|/' | awk -F '|' "{print \"('\" \$2 \"', '\" \$1 \"', '\" \$1 \" - \" \$2 \"'),\";}" |
--     sed -e "s/' /'/g" -e "s/ '/'/g" -e "s/'s/''s/g" )

create table track (
  id SERIAL,
  title text not null,
  artist_id integer not null,
  album_id integer not null,
  path text not null,
  duration_secs integer,
  duration_is_estimate boolean,

  primary key (id),
  unique(path, album_id),
  unique(title, artist_id),

  foreign key (artist_id) references artist(id),
  foreign key (album_id) references album(id)
);
comment on column track.path is 'relative to album.path';

create table playlist_entry (
  playlist_id integer,
  entry_order integer check (entry_order >= 0),
  track_id integer,
  child_playlist_id integer,

  primary key (playlist_id, entry_order),

  check (coalesce(track_id, child_playlist_id) is not null),

  foreign key (playlist_id) references playlist(id),
  foreign key (track_id) references track(id),
  foreign key (child_playlist_id) references playlist(id)
);


