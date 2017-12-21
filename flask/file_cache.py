#!/usr/bin/env python
import sys
import logging
import psycopg2
import requests
import os
from datetime import date, datetime
import subprocess

# keep in sync with cache_status in db/init.sql
ST_INIT=0
ST_DOWNLOADING=1
ST_COMPLETE=2
ST_ERROR=3
ST_EXPIRED=4

class FileCache:
  def __init__(self, connParams, cacheRoot):
    self.connParams = connParams
    self.cacheRoot = cacheRoot
    self._getCacheMeta()
    # defaults
    self.maxAgeInDays = 90
    self.minFreePercent = 10
    self.maxCachedBytes = 10*1024*1024*1024 # 10GB
    self.maxAttempts = 3

  def setMaxAge(self, ageInDays):
    self.maxAgeInDays = ageInDays

  def setMinFreePercent(self, percent):
    self.minFreePercent = percent

  def expire(self):
    logging.info('expiring items older than {} days'.format(self.maxAgeInDays))
    map(lambda meta: self._expireOne(meta), self.cache.values())
       
  def _expireOne(self, meta):
    if(getAgeInDays(meta) > self.maxAgeInDays):
      logging.info('removing expired item: ' + str(meta))
      self._deleteEntry(meta)

  def _deleteEntry(self, meta):
    path = meta['path']
    if(os.access(path, os.R_OK)):
      os.remove(meta['path'])
    del self.cache[meta['url']]
    self._executeSql('UPDATE file_cache set state = %s where url = %s',[ST_EXPIRED, meta['url']])

  def getUrl(self, url):
    if url in self.cache and self.cache[url]['state'] == ST_COMPLETE:
      now = datetime.today()
      self._executeSql('UPDATE file_cache set last_read = %s where url = %s',[now, url])
      self.cache[url]['last_read'] = now
      return self.cache[url]
    else:
      return None


  def purgeExpired(self, group, currentItems):
    logging.info('purging ' + group)
    result = self._executeSql('DELETE FROM file_cache where state = %s and source_group = %s and not %s @> ARRAY[ url ]', [ST_EXPIRED, group, currentItems])
    logging.debug('purge result: ' + str(result))
    return result

  def preFetch(self, url, group):
    logging.info('checking ' + url)
    if(url in self.cache):
      meta = self.cache[url]
      state = meta['state']
      if(state == ST_COMPLETE or state == ST_DOWNLOADING):
        logging.debug('already cached  or in progress: {}'.format(state))
        return False
      # have entry but something went wrong last time - do we keep trying?
      attempts = meta['attempts']
      if(attempts >= self.maxAttempts):
        logging.warn('already attempted to prefetch {} {} times, giving up'.format(url, attempts))
        return False
      fullpath = meta['path']
    else:
      (pathDir,filename) = self._createCacheRecord(url, group)
      if(not os.access(pathDir, os.W_OK)):
        os.makedirs(pathDir, 0755)
      fullpath = '{}/{}'.format(pathDir,filename)
      attempts = 0
    logging.info("fetching content-length")
    with requests.head(url, allow_redirects=True) as r:
      if(r.status_code == 200):
	expectedSize = int(r.headers['content-length'])
    self._makeRoomFor(expectedSize)
    logging.info("fetching content")
    self._executeSql('UPDATE file_cache set state = %s where url = %s',[ST_DOWNLOADING, url])
    size=0
    try:
      with requests.get(url, allow_redirects=True, stream=True) as r:
        if(r.status_code == 200):
	   expectedSize = int(r.headers['content-length'])
           with open(fullpath, 'wb') as f:
             chunks=0
             total=0
             start=datetime.now()
             origStart=start
             lastTotal=0
             for chunk in r.iter_content(chunk_size=16*1024):
               f.write(chunk)
               chunks=chunks+1
               total=total+len(chunk)
               if(chunks%100 == 0):
                 end=datetime.now()
                 kbits=(total-lastTotal)*8.0/1024.0
                 td=(end-start)
                 tdSecs=(td.seconds*1000000.0+td.microseconds)/1000000.0
                 kbps=(kbits/tdSecs)
                 rate=getKbps(start, end, total-lastTotal)
                 start=end
                 lastTotal=total
                 overallRate=getKbps(origStart, end, total)
                 logging.debug('read {} chunks, total of {} bytes - last rate: {}kbps overall rate: {}kbps'.format(chunks,total,rate,overallRate))
        else:
          raise Exception('result was {}, not 200'.format(r.status_code))
      size = os.stat(fullpath).st_size
      if(size != expectedSize):
        raise Exception('bad size for {}: {} - expected {}'.format(fullpath, size, expectedSize))
    except Exception as ex:
      logging.error("\n\nerror while fetching {}: {}\n\n".format(url, str(ex)))
      self._executeSql('UPDATE file_cache set state = %s, size = %s, attempts = %s where url = %s',[ST_ERROR, size, attempts + 1, url])
      return False
    self._executeSql('UPDATE file_cache set state = %s, size = %s where url = %s',[ST_COMPLETE, size, url])
    self.cache[url] = {
      'url': url,
      'state': 2,
      'size': size,
      'last_read': None,
      'attempts': 1,
      'path': fullpath,
      'created': datetime.today()
    }
    logging.info('Successfully preFetched {}'.format(url))
    return True

  def _getFreeSpace(self, newBytes):
    # os.statvfs gives us the data
    stat = os.statvfs(self.cacheRoot)
    neededBlocks = (newBytes - 1)/stat.f_frsize + 1
    avail = stat.f_bavail - neededBlocks
    freePct = float(avail)/float(stat.f_blocks)*100
    # du -s -B1 /data/musicserver/cache/
    output = subprocess.check_output(['du', '-s', '--block-size', '1', self.cacheRoot])
    usedBytes = int(output.split(None)[0])
    logging.debug('bytes: {} -> blocks {}, current avail: {}, new avail {}, new freePct {}, used bytes {}'.
	format(newBytes, neededBlocks, stat.f_bavail, avail, freePct, usedBytes))
    return freePct, usedBytes + newBytes

  def _makeRoomFor(self, newBytes):
    (freePct, bytesUsed) = self._getFreeSpace(newBytes)
    while (freePct < self.minFreePercent or bytesUsed > self.maxCachedBytes):
      # remove next file
      meta = self._getNextToPurge()
      if(not meta):
        logging.debug('could not find any to purge in _makeRoomFor')
        return
      logging.debug('purging ' + str(meta))
      self._deleteEntry(meta)
      (freePct, bytesUsed) = self._getFreeSpace(newBytes)
  
  def _getNextToPurge(self):
    # TODO only sort once (when do we need to re-sort?)
    # TODO better sort
    # for now, just go with oldest
    byCreated = sorted(self.cache.values(), key = lambda meta: meta['created'])
    if(len(byCreated) == 0):
      return None
    return byCreated[0]

  def _createCacheRecord(self, url, group):
    with psycopg2.connect(self.connParams) as conn, conn.cursor() as cursor:
      cursor.execute('INSERT INTO file_cache(url, source_group) VALUES (%s, %s) RETURNING id',[url, group])
      conn.commit()
      id = cursor.fetchone()[0]
      idStr='{:08x}'.format(id)
      pathDir='{}/{}/{}'.format(idStr[0:2], idStr[2:4], idStr[4:6])
      filename=idStr[6:8]
      path = pathDir + '/' + filename
      cursor.execute('UPDATE file_cache set path = %s where id = %s',[path, id])
      conn.commit()
    return ('{}/{}'.format(self.cacheRoot, pathDir), filename)

  def _cacheRow(self, metaData):
    self.cache[metaData[0]] = {
      'url': metaData[0],
      'state': metaData[1],
      'size': metaData[2],
      'last_read': metaData[3],
      'attempts': metaData[4],
      'path': self.cacheRoot + '/' + metaData[5],
      'created': metaData[6]
    }
   
  def _getCacheMeta(self):
    # keys are urls
    self.cache = {}
    self._executeSql('select url, state, size, last_read, attempts, path, created from file_cache', None,
      self._cacheRow)
    logging.debug('loaded {} urls from cache'.format(len(self.cache)))

  def _executeSql(self, sql, params, rowFunc=None):
    with psycopg2.connect(self.connParams) as conn, conn.cursor() as cursor:
      cursor.execute(sql, params)
      if(rowFunc):
        row = cursor.fetchone()
        while row:
          rowFunc(row)
          row = cursor.fetchone()
      conn.commit()

def getAgeInDays(meta):
  if(meta['last_read']):
    start=meta['last_read']
  else:
    start=meta['created']
  td = date.today() - start.date()
  logging.debug('age of {}: {}'.format(meta['url'], td))
  return td.days

def getKbps(startTime, endTime, sizeInBytes):
  kbits=sizeInBytes*8.0/1024.0
  td=(endTime-startTime)
  tdSecs=(td.seconds*1000000.0+td.microseconds)/1000000.0
  return kbits/tdSecs
