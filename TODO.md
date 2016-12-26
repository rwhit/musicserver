- nprOne
  see ~/nprOne & additions to server.py
  - cache reco metadata
  - main screen should start auto-playing
  - pre-download recommendations (really need to build support for starting a download and playing before it completes)
    - read url & stream to both file & then (equiv of) tail -f  | mplayer
      This works:
        curl -s https://ondemand.npr.org/npr-mp6/npr/newscasts/2016/09/05/newscastShort090632.mp4 >/tmp/news.mp4 &
          (tail --pid $! -n +1 -f /tmp/news.mp4 | mplayer -)
- have volume control everywhere
- have system volume control
  see amixer and alsactl
- "what's on" page to bring to current state
