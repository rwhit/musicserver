from mediaplayerController import get_mediaplayer
import time
import os

track_duration=-1
def cb(meta, duration,pos):
    global track_duration
    track_duration=duration
    print('{}:{} of {}'.format(str(meta), pos, duration))

mp = get_mediaplayer('/tmp/mplayer')
mp.play(os.getenv('Rest'), statusCallback=cb)
time.sleep(6)
if(track_duration):
    mp.write('seek {} 2'.format(track_duration - 6))
time.sleep(10)
mp.close()
