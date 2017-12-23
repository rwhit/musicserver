#!/usr/bin/env python3
import logging
FORMAT = '%(asctime)-15s:%(name)s:%(levelname)s:%(message)s:%(funcName)s:%(module)s:%(lineno)d'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
import sys
import argparse
# inject this!
sys.path.append('/home/pi/musicserver/flask')
from podcastController import PodcastController as PC
from file_cache import FileCache

def stop():
  sys.exit(0)

def main():
  # inject these too! - or pull from config
  connParams='dbname=pi user=pi'
  cacheRoot='/data/musicserver/cache'
  defaultMaxToFetch=20

  parser = argparse.ArgumentParser(description='Prefetch podcasts')
  parser.add_argument('-m', '--maxToFetch', default=defaultMaxToFetch, type=int)
  args = parser.parse_args()
  logging.info('maxToFetch: {}'.format(args.maxToFetch))

  pc = PC()
  cache = FileCache(connParams, cacheRoot)
  logging.info('pre-expire size: {}'.format(len(cache.cache.keys())))
  cache.expire()
  logging.info('post-expire size: {}'.format(len(cache.cache.keys())))
  count = 0
  for feed in pc.get_feeds():
    logging.info('Checking ' + feed[0])
    feedUrl = feed[1]
    items = pc.get_feed(feedUrl)['items']
    cache.purgeExpired(feedUrl, [item['guid'] for item in items])
    for item in items:
      if(cache.preFetch(item['guid'], feedUrl)):
        count = count + 1
        logging.debug('count now ' + str(count))
        if(count >= args.maxToFetch):
          logging.info('fetched ' + str(args.maxToFetch) + ' item(s) - stopping')
          stop()
  stop()


if __name__ == '__main__':
  main()
