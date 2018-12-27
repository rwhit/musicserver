import time

class BaseController(object):
    def __init__(self):
        self.volume = 5
        self.paused = False
        self.elapsedTime = 0
        self.startTime = time.time()

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.elapsedTime = self.elapsedTime + time.time() - self.startTime
        else:
            self.startTime = time.time()
        return self.paused
    
    def is_paused(self):
        return self.paused

    def get_time(self):
        if self.paused:
            return self.elapsedTime
        else:
            return self.elapsedTime + time.time() - self.startTime

    def get_volume(self):
        return self.volume

