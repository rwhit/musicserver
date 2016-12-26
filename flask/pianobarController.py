from baseController import BaseController
import subprocess
import os
import time

class PianobarController(BaseController):
    def __init__(self):
        BaseController.__init__(self)
        self.check_status()
        self.writer = open(os.environ["HOME"] + "/.config/pianobar/ctl", "a")
        self.latest = ""

    def check_status(self):
        try:
            subprocess.check_call(['ps', '-C', 'pianobar'])
        except subprocess.CalledProcessError:
            #Pianobar is not running
            self.volume = 5
            self.paused = False
            self.elapsedTime = 0
            self.startTime = time.time()
            subprocess.Popen(['pianobar'], close_fds=True)

    def set_latest(self, action, data):
        if action == "songstart":
            self.elapsedTime = 0
            self.startTime = time.time()
        self.latest = data

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

