from string import split
from urllib2 import urlopen,unquote
from urllib import urlretrieve
from mediaplayerController import get_mediaplayer
from baseController import BaseController
from file_cache import FileCache
from tempfile import mkstemp
import xml.etree.ElementTree as ET
import os
import time
import psycopg2
import logging
import subprocess

class PodcastController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.paused = True
        self.elapsedTime = 0
        self.startTime = time.time()
	self.cache = FileCache('dbname=pi user=pi', '/data/musicserver/cache')

    def get_feeds(self):
        feeds = []
        conn = None
        try:
            conn = psycopg2.connect('dbname=pi user=pi')
            with conn.cursor() as cursor:
                cursor.execute('select label, url, id from podcast_feeds order by rank asc')
                feedData = cursor.fetchone()
                while feedData:
                    feeds.append(feedData)
                    feedData = cursor.fetchone()
        finally:
            conn.close()
        return feeds

    def get_feed(self, url):
        feedData = None
        try:
            namespaces = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
            logging.info("orig url: " + url)
            url=unquote(url)
            logging.info("decoded: " + url)
            feedData = urlopen(url)
            channel = ET.parse(feedData).getroot().find('channel')
            feed = dict()
            feed['title'] = channel.find("title").text
            feed['image'] = channel.find("image").find("url").text
            feed['items'] = []
            for item in channel.findall("item"):
                feedItem = dict()
                feedItem['title'] = item.find('title').text
                durationHolder = item.find('itunes:duration',namespaces)
                duration = None
                if durationHolder is not None:
                  duration = durationHolder.text
                if duration is not None:
                  logging.debug("duration: " + str(duration))
                  feedItem['duration'] = duration
                  parts = duration.split(':')
                  if(len(parts) >= 2):
                    feedItem['durationSecs'] = int(parts[0]) * 60 + int(parts[1])
                  elif(len(parts) == 1):
                    feedItem['durationSecs'] = int(parts[0])
                  else:
                    feedItem['durationSecs'] = 99
                else:
                  logging.warn("could not find duration in: " + str(item))
                  feedItem['duration'] = 99
                  feedItem['durationSecs'] = 99
                #feedItem['guid'] = item.find('guid').text
                feedItem['guid'] = item.find('enclosure').get('url')
                feed['items'].append(feedItem)
        finally:
            if(feedData): feedData.close()
        return feed

    def play_podcast(self, url, duration, durationSecs, title):
        mp = get_mediaplayer()
        logging.info("orig url: " + url)
        url=unquote(url)
        logging.info("decoded: " + url)
        fd = None
        try:
          cached = self.cache.getUrl(url)
	  if(cached):
            tmpFile = cached['path']
            logging.info("cached: " + tmpFile)
	  else:
            (fd,tmpFile) = mkstemp()
            logging.info("downloading to: " + tmpFile)
            #urlretrieve(url,tmpFile)
            #subprocess.check_call(["curl","-L","-s",url],stdout=fd)
            curlCmd="curl -L -s '" + url + "' >" + tmpFile
            logging.info("via: " + curlCmd)
            subprocess.check_call(["bash", "-c", curlCmd])
          tmpFileUrl = 'file://' + tmpFile
          mp.play(tmpFileUrl)
          self.paused = False
          self.elapsedTime = 0
          self.startTime = time.time()
          return { 'duration': duration,
                   'durationSecs': durationSecs,
                   'title': title }
        finally:
          if(fd):
            os.close(fd)
            # give mediaplayer a chance to open it first
#            for tries in range(300):
#                time.sleep(.1)
#                if(self.processHasOpened(mp.getPid(), tmpFile)):
#                    break
#            os.remove(tmpFile)

    def swap(self, id1str, id2str):
        id1 = int(id1str)
        id2 = int(id2str)
        logging.info("swapping " + id1str + " and " + id2str)
        ranks = {}
        conn = None
        try:
            conn = psycopg2.connect('dbname=pi user=pi')
            with conn.cursor() as cursor:
                cursor.execute('select id, rank from podcast_feeds where id in (%s,%s)', [id1, id2]);
                feedData = cursor.fetchone()
                ranks[feedData[0]] = feedData[1]
                feedData = cursor.fetchone()
                ranks[feedData[0]] = feedData[1]
                cursor.execute('update podcast_feeds set rank = %(rank)s where id = %(id)s', { 'id': id1, 'rank': ranks[id2] })
                cursor.execute('update podcast_feeds set rank = %(rank)s where id = %(id)s', { 'id': id2, 'rank': ranks[id1] })
                conn.commit()
        finally:
             conn.close()


    # override
    def pause(self):
        self.write('pause')
	BaseController.pause(self)

    # write straight to mplayer fifo
    def write(self, message):
        get_mediaplayer().write(message)
                
    def processHasOpened(self, pid, fname):
        d = "/proc/%s/fd/" % pid
        try:
            for fd in os.listdir(d):
                f = os.readlink(d+fd)
                if (f == fname):
                    return True
        except OSError:
            return True
        return False
           
    
