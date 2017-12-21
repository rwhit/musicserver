#!/usr/bin/env python3
import logging
FORMAT = '%(asctime)-15s:%(name)s:%(levelname)s:%(message)s:%(funcName)s:%(module)s:%(lineno)d'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
import sys
import argparse
import os
import subprocess
# inject this (if we need it)!
sys.path.append('/home/pi/musicserver/flask')
from musicServerConfig import MusicServerConfig as Config
from connFactory import ConnFactory

class NotAlbum(Exception):
  pass

class Importer:
  def __init__(self, config):
    self.config = config
    self.conn = ConnFactory(config).getConnection()

  def close(self):
    self.conn.close()

  def processDir(self, topDir):
    for dir, subdirs, files in os.walk(topDir):
      logging.debug('processing %s', os.path.basename(dir))
      try:
        self.importAlbum(dir, files)
      except NotAlbum: 
        logging.info('%s does not appear to be an album, skipping', dir)

  def importAlbum(self, dir, files):
    try:
      (artist,title) = os.path.basename(dir).split(' - ', maxsplit=1)
    except ValueError as ve:
      raise NotAlbum(dir) from ve
    logging.debug("\nartist: %s\ntitle: %s", artist, title)
    artistId = self.ensureArtist(artist)
    (albumId, playlistId) = self.newAlbum(artistId, title, dir)
    # lists of (trackId,duration)
    providedPlaylist = None
    playlistEntries = []
    for filename in files:
      fullpath = '/'.join((dir,filename))
      if(self.isPlaylist(fullpath)):
        providedPlaylist = self.importPlaylist(albumId, fullpath)
      else:
        (artist,title,duration) = self.parseMetaFromFilename(filename)
        playlistEntries.append(self.ensureTrack(albumId, filename, artist, title, duration))
    self.importPlaylistEntries(playlistId, playlistEntries, providedPlaylist)

  def ensureArtist(self, artist):
    logging.info("ensureArtist {}".format(artist))
    def txn(cur):
      cur.execute('insert into artist (name) values (%s) on conflict(name) do update set name = %s returning id', (artist,artist))
      id = cur.fetchone()[0]
      return id
    return self.simpleTransaction(txn)

  # returns (albumId, playlistId)
  def newAlbum(self, artistId, title, dir):
    logging.info("newAlbum(%d,%s,%s)", artistId, title, dir)
    def txn(cur):
        cur.execute("insert into playlist (name, type) values(%s, 'album') returning id", (title,))
        playlistId = cur.fetchone()[0]
        cur.execute("insert into album(title, artist_id, playlist_id, path) values(%s,%s,%s,%s) returning id",
                (title, artistId, playlistId, dir))
        albumId = cur.fetchone()[0]
        return (albumId, playlistId)
    return self.simpleTransaction(txn)

  def simpleTransaction(self, txn):
    try:
      with self.conn.cursor() as cur:
        result = txn(cur)
        self.conn.commit();
    finally:
      self.conn.rollback()
    return result


  # returns (trackId, duration), duration may be None
  def ensureTrack(self, albumId, filename, artist, title, duration):
    logging.info("ensureTrack(%d,%s,%s,%s,%s)", albumId, filename, artist, title, str(duration))
    artistId = self.ensureArtist(artist)
    def txn(cur):
      cur.execute("""insert into track (title, artist_id, album_id, path, duration_secs)
                     values(%s,%s,%s,%s,%s)
                     on conflict (path, album_id) do update set duration_secs = coalesce(track.duration_secs, excluded.duration_secs)
                     returning id, duration_secs""",
                  (title, artistId, albumId, filename, duration))
      results = cur.fetchone()
      return (results[0], results[1])
    return self.simpleTransaction(txn)

  # returns list of (trackId, duration)
  def importPlaylist(self, albumId, filename):
    logging.info("importPlaylist(%s)", filename)
    entries=[]
    meta=None
    with open(filename) as fh:
        for line in fh:
            if(line[0] == '#'):
                meta = self.parseMetaComment(line)
            elif(not meta):
                meta = self.parseMetaFromFilename(line)
            else:
                logging.debug('meta: %s', str(meta))
                (artist,title,duration) = meta
                logging.debug('unpacked: %s,%s,%s', artist, title, str(duration))
                # todo strip lf from line
                filename = line.strip()
                trackTuple = self.ensureTrack(albumId, filename, artist, title, duration)
                entries.append(trackTuple)
                meta=None
    return entries

  # return (artist, title, duration)
  def parseMetaComment(self, line):
    logging.info("parseMetaComment(%s)", line)
    # sample metadata:
    # #EXTINF:141,Steven Curtis Chapman - Happy New Year
    if(not line.startswith('#EXTINF:')):
        return None
    (duration,rest)=line[8:].split(',', maxsplit=1)
    (artist,title)=rest.split(' - ', maxsplit=1)
    logging.debug("%s -> (%s,%s,%s)", line, artist,title,duration)
    return (artist,title.rstrip(),int(duration))

  def parseMetaFromFilename(self, line):
    logging.info("parseMetaFromFilename(%s)", line)
    base = os.path.basename(line).rsplit('.', maxsplit=2)[0]
    parts = base.split(' - ', maxsplit=2)
    if(len(parts) == 3):
        return(parts[1], parts[2], None)
    else:
      return(parts[0], parts[1], None)

  def importPlaylistEntries(self, playlistId, playlistEntries, providedPlaylistEntries):
    logging.error("Implement importPlaylistEntries(%d,%s,%s)", playlistId, str(playlistEntries), str(providedPlaylistEntries))
    return 

  def isPlaylist(self, filename):
    cp = subprocess.run(['file',filename], stdout=subprocess.PIPE)
    logging.debug('file %s: %s',filename, str(cp.stdout))
    if(cp.stdout and 'text' in str(cp.stdout).lower()):
        return True
    return False

def main():
  topDir = sys.argv[1]
  config = Config()
  importer = Importer(config)
  try:
    importer.processDir(topDir)
  finally:
    importer.close()

if __name__ == '__main__':
  main()
