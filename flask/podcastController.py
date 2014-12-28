from string import split
from urllib2 import urlopen
from mediaplayerController import get_mediaplayer
from baseController import BaseController
import xml.etree.ElementTree as ET
import time
import psycopg2
import logging

class PodcastController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.paused = True
        self.elapsedTime = 0
        self.startTime = time.time()

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
        try:
            namespaces = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
            feedData = urlopen(url)
            channel = ET.parse(feedData).getroot().find('channel')
            feed = dict()
            feed['title'] = channel.find("title").text
            feed['image'] = channel.find("image").find("url").text
            feed['items'] = []
            for item in channel.findall("item"):
                feedItem = dict()
                feedItem['title'] = item.find('title').text
                duration = item.find('itunes:duration',namespaces).text
                feedItem['duration'] = duration
                parts = duration.split(':')
                feedItem['durationSecs'] = int(parts[0]) * 60 + int(parts[1])
                feedItem['guid'] = item.find('guid').text
                feed['items'].append(feedItem)
        finally:
            feedData.close()
        return feed

    def play_podcast(self, url, duration, durationSecs, title):
        mp = get_mediaplayer()
        mp.play(url)
        self.paused = False
        self.elapsedTime = 0
        self.startTime = time.time()
        return { 'duration': duration,
                 'durationSecs': durationSecs,
                 'title': title }

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
                
           
    
