from subprocess import Popen,PIPE
import logging
import threading
from time import time, sleep
from os.path import basename

logging.basicConfig(level=logging.DEBUG)

DEFAULT_FIFO = '/home/pi/mediaplayer/fifo'
class MediaplayerController():
    # states
    ST_NOCHILD='nochild'
    ST_IDLE='idle'
    ST_STARTING='starting'
    ST_PLAYING='playing'
    ST_EXPECTING_TIME_POS='exp-time-pos'
    ST_EXPECTING_LENGTH='exp-length'

    TRACK_META = frozenset(('title','artist','album','album_artist'))

    def __init__(self, fifo=DEFAULT_FIFO):
        self.fifoName = fifo
        self.process = None
        self.fifo = None
        self.cmd = None
        self.state = self.ST_NOCHILD
        self._clearMeta()

    def _clearMeta(self):
        self.url = None
        self.pos = None
        self.posWhen = None
        self.duration = None
        self.emptyLineCount = 0
        self.trackMeta = {}

    def play(self, url, statusCallback=None, statusFreqSecs=5):
        logging.debug("MPC: playing " + url)
        self.url = url
        self.statusCallback = statusCallback
        self.statusFreqSecs = statusFreqSecs
        self._clearMeta()
        # best guess for now - _processStdout will update if it can
        self.trackMeta['title'] = basename(url)
        if not self.process:
            # -idle will allow no url
            # self.cmd = 'mplayer -quiet -noconsolecontrols -slave -input file={0} {1}'.format(self.fifoName, url)
            self.cmd = 'mplayer -quiet -noconsolecontrols -slave -input file={0} -idle'.format(self.fifoName)
            with open('/dev/null') as DEVNULL:
                self.process = Popen(args = self.cmd, shell = True, stdin=DEVNULL, stdout=PIPE, close_fds=True)
            self.fifo = open(self.fifoName, 'w')
            self.state = self.ST_IDLE
            self.stdoutThread = threading.Thread(target=self._processStdout,name='mplayer-stdout')
            self.stdoutThread.start()
            self.updateThread = threading.Thread(target=self._updateLoop,name='mplayer-update')
            self.updateThread.start()
        #else:
            #self._message("loadfile " + url)
        self.state = self.ST_STARTING
        self._message("loadfile \"{}\"".format(url))

    def _message(self, msg):
        self.fifo.write(msg)
        self.fifo.write("\n")
        self.fifo.flush()

    def downloadAndPlay(self, url):
        logging.debug("MPC: downloading & playing " + url)
        self._downloadAndPlay(url)

    # see http://www.mplayerhq.hu/DOCS/tech/slave.txt for commands
    def write(self, message):
        if self.process:
            self._message(message)

    def close(self):
        if self.process:
            self._message('quit')

    def getPid(self):
        if self.process:
            return self.process.pid

    def _processStdout(self):
        for line in self.process.stdout:
            # handle Exiting
            #DEBUG:root:MPC:mplayer-stdout:idle:b'Exiting... (Quit)\n':None
            if(line.startswith(b'Exiting... ')):
                self._mplayerExited()
            elif(line.startswith(b' ') and (self.state == self.ST_IDLE or self.state == self.ST_STARTING)):
                #DEBUG:root:MPC:mplayer-stdout:starting:b'Clip info:\n':None
                #DEBUG:root:MPC:mplayer-stdout:b" title: Alice's Restaurant Massacree\n"
                #DEBUG:root:MPC:mplayer-stdout:b' artist: Arlo Guthrie\n'
                #DEBUG:root:MPC:mplayer-stdout:b' album_artist: Arlo Guthrie\n'
                #DEBUG:root:MPC:mplayer-stdout:b" album: Alice's Restaurant\n"
                self._processTrackMeta(line[1:])
            elif(line.startswith(b'Starting playback')):
                self.state = self.ST_PLAYING
                self.pos = 0
                self.posWhen = time()
                if(not self.duration):
                    self._message('get_property length')
            elif(self.state == self.ST_PLAYING or self.state.startswith('exp-')):
                if(line == "\n"):
                    self.emptyLineCount+=1
                    if(self.emptyLineCount == 3):
                        self._playbackEnded()
                else:
                    self.emptyLineCount = 0
                    # TODO? generalize ANS_<PROPERTY>
                    if(line.startswith(b'ANS_length=')):
                        # b'ANS_LENGTH=1117.00\n'
                        dot=line.index(b'.', 11)
                        self.duration = int(line[11:dot])
                        if(self.pos == None):
                            self.pos = 0
                            self.posWhen = time()
                        self.state = self.ST_PLAYING
                        self._sendStatusUpdate()
                    elif(line.startswith(b'ANS_time_pos=')):
                        # b'ANS_TIME_POSITION=963.3\n'
                        dot=line.index(b'.', 13)
                        self.pos = int(line[13:dot])
                        self.posWhen = time()
                        self.state = self.ST_PLAYING
                        self._sendStatusUpdate()
                    elif(line == b'ANS_ERROR=PROPERTY_UNAVAILABLE\n'):
                        # b'ANS_ERROR=PROPERTY_UNAVAILABLE\n'
                        if(self.state == self.ST_EXPECTING_TIME_POS):
                            self._playbackEnded()
                        else:
                            self.state = self.ST_PLAYING
                    else:
                        logging.debug('Unrecognized line in ST_PLAYING')
            else:
                logging.debug('Unrecognized line, state = %s', self.state)

            logging.debug("MPC:mplayer-stdout:%s:%s:%s",self.state,str(line),_safeInt(self.pos))
            if(self.state == self.ST_NOCHILD):
                logging.debug('_processStdout exiting')
                return

    def _processTrackMeta(self, line):
        #DEBUG:root:MPC:mplayer-stdout:b" title: Alice's Restaurant Massacree\n"
        #DEBUG:root:MPC:mplayer-stdout:b' artist: Arlo Guthrie\n'
        #DEBUG:root:MPC:mplayer-stdout:b' album_artist: Arlo Guthrie\n'
        #DEBUG:root:MPC:mplayer-stdout:b" album: Alice's Restaurant\n"
        (prop,value) = [part.decode('utf-8') for part in line.split(b':', maxsplit=1)]
        prop=prop.lower()
        if(prop in self.TRACK_META):
            self.trackMeta[prop] = value.strip()
        else:
            logging.debug('untracked property: "%s"', prop)

    def _playbackEnded(self):
        logging.debug('_playbackEnded')
        self.state = self.ST_IDLE
        self._clearMeta()
        self._sendStatusUpdate()

    def _sendStatusUpdate(self):
        if(self.statusCallback):
            # TODO offset pos based by (time() - self.posWhen), to max of duration
            self.statusCallback(self.trackMeta, self.duration, self.pos)

    def _mplayerExited(self):
        self._playbackEnded()
        logging.debug('_mplayerExited')
        self.state = self.ST_NOCHILD
        self.process = None
        self.fifo = None
        self.cmd = None
        self.url = None

    def _updateLoop(self):
        while self.state != self.ST_NOCHILD:
            sleep(self.statusFreqSecs)
            if(self.state == self.ST_PLAYING and self.statusCallback):
                self._message('get_property time_pos')
        logging.debug('_updateLoop exiting')

def _safeInt(val):
    if(val == None):
        return 'None'
    else:
        return str(val)

MEDIAPLAYER = None
def get_mediaplayer(fifo=DEFAULT_FIFO):
    global MEDIAPLAYER
    if not MEDIAPLAYER:
        MEDIAPLAYER = MediaplayerController(fifo)
    return MEDIAPLAYER
