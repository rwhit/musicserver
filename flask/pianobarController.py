from baseController import BaseController
import subprocess
import os
import time
import logging

class PianobarController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.subproc = None
        self.check_status()
        self.baseDir = os.environ["HOME"] + "/.config/pianobar"
        self.writer = open(self.baseDir + "/ctl", "a")
        self.latest = ""
        self.monitorProc = None

    def check_status(self):
        if(not self.subproc or self.subproc.poll()):
            #Pianobar is not running
            self.volume = 5
            self.paused = False
            self.elapsedTime = 0
            self.startTime = time.time()
            self.subproc = subprocess.Popen(['pianobar'], close_fds=True)

    def _restart(self):
        if(self.subproc and not self.subproc.poll()):
            self.subproc.terminate()
            self.subproc.wait()
            self.subproc = None
        self.check_status()

    def set_latest(self, action, data):
        self.latest = data
        if action == 'RESTART':
            self._restart()
        elif action == "songstart":
            self.elapsedTime = 0
            self.startTime = time.time()
            self.duration = int(data['songDuration'])
            self._startMonitor()
        elif action == "songfinish":
            self._stopMonitor()

    def get_latest(self):
        return self.latest

    def write(self, message):
        self.writer.write(message)
        self.writer.flush()

    def set_volume(self, volume):
        difference = abs(volume - self.volume)
        char = "("
        if volume > self.volume:
            char = ")"
        message = char * difference
        self.write(message)
        self.volume = volume

    def pause(self):
       BaseController.pause(self)
       self._toggleMonitorPause()

    def _startMonitor(self):
       logging.debug('_startMonitor - duration: {0}'.format(self.duration))
       if(self.monitorProc):
           logging.error('previous monitor running, killing it')
           self.monitorProc.kill()
       extra = min(30, self.duration/10)
       maxSecs = self.duration + extra
       cmd='sleep {0} && {1}/eventcmd.py RESTART'.format(maxSecs, self.baseDir)
       self.monitorProc = subprocess.Popen([cmd],shell=True,close_fds=True)

    def _stopMonitor(self):
       logging.debug('_stopMonitor')
       if(self.monitorProc):
           self.monitorProc.kill()
           self.monitorProc = None

    def _toggleMonitorPause(self):
       logging.debug('_toggleMonitor - paused: {0}'.format(self.is_paused()))
       if(self.is_paused()):
         # set remainin duration
         self.duration = self.duration - (time.time() - self.startTime)
         self._stopMonitor()
       else:
         self._startMonitor()
