from subprocess import Popen
import logging
import requests
import time
logging.basicConfig(level=logging.DEBUG)

class MediaplayerController():
    def __init__(self, config):
        '''
        config is map, with these required values:
        - mplayerPushUrl - target for mplayerController.pushStatus
        - mpcUrl - url mplayerController listens on
        - mpcPath - to invoke mplayerController
        '''
        self.process = None
        self.url = None
        self.cmd = None
        self.config = config

    def _open(self, url):
        self.url = url
        if not self.process:
            self.cmd = [ self.config['mpcPath'] ]
            with open('/dev/null') as DEVNULL:
                self.process = Popen(args = self.cmd, shell = False, stdin=DEVNULL, close_fds=True)
                # give it a chance to start
                # TODO actually poll for port to be bound
                time.sleep(.1)
            self._command('PushStatus', {'url': self.config['mplayerPushUrl'], 'freqSecs': 5})
        # TODO send /Play?url=url
        self._command('Play', {'url': url})
        
    def _command(self, cmd, argMap=[]):
        url = self.config['mpcUrl'] + cmd
        logging.debug('POSTing to {}'.format(url))
        requests.post(url, data=argMap)

    def play(self, url):
        logging.debug("MPC: playing " + url)
        self._open(url)

    def pause(self):
        logging.debug("MPC: pausing")
        self._command('Pause')

    def resume(self):
        logging.debug("MPC: resuming")
        self._command('Resume')

    def close(self):
        if self.process:
            self._message('quit')
            self.process = None
            self.fifo = None
            self.url = None
            self.cmd = None

    def getPid(self):
        if self.process:
            return self.process.pid
            

MEDIAPLAYER = None
def get_mediaplayer(config):
    global MEDIAPLAYER
    if not MEDIAPLAYER:
        MEDIAPLAYER = MediaplayerController(config)
    return MEDIAPLAYER
