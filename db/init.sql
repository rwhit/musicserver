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

