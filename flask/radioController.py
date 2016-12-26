from mediaplayerController import get_mediaplayer
from baseController import BaseController
import psycopg2
import time

class RadioController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.volume = 5
        self.station = ''

    def _getStations(self):
        stations = []
        with psycopg2.connect('dbname=pi user=pi') as conn:
            with conn.cursor() as cursor:
                cursor.execute('select label, url from radio_stations order by rank asc')
                stationData = cursor.fetchone()
                while stationData:
                    stations.append(stationData)
                    stationData = cursor.fetchone()
        return stations
    
    def play(self, url, station):
        mp = get_mediaplayer()
        mp.play(url)
        self.paused = False
        self.elapsedTime = 0
        self.startTime = time.time()
        self.station = station

    def get_latest(self):
        return { 'current_station': self.station,
                 'stations': self._getStations() }

    # override
    def pause(self):
        self.write('pause')
	BaseController.pause(self)

    # write straight to mplayer fifo
    def write(self, message):
        get_mediaplayer().write(message)
                
