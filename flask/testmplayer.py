from mediaplayerController import get_mediaplayer
import time

mp = get_mediaplayer()
mp.play('http://podcastdownload.npr.org/anon.npr-podcasts/podcast/510298/370241211/npr_370241211.mp3')
time.sleep(10)
mp.play('http://podcastdownload.npr.org/anon.npr-podcasts/podcast/510298/368629849/npr_368629849.mp3?duration=52:18')
time.sleep(10)
mp.close()
