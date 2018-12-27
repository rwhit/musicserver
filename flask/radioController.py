from mediaplayerController import get_mediaplayer
from baseController import BaseController
import psycopg2
import time

class RadioController(BaseController):
    def __init__(self, config):
        '''
        config - see mediaplayerController.__init__
        '''
        # TODO get this working
        # super(RadioController, self).__init__()
        BaseController.__init__(self)
        self.volume = 5
        self.station = ''
        self.config = config

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
        self.mp = get_mediaplayer(self.config)
        self.mp.play(url)
        self.paused = False
        self.elapsedTime = 0
        self.startTime = time.time()
        self.station = station

    def get_latest(self):
        return { 'current_station': self.station,
                 'stations': self._getStations() }

    # override
    def pause(self):
	s = super(RadioController, self)
        isPaused = s.pause()
        if isPaused:
            self.mp.pause()
        else:
            self.mp.resume()
                
