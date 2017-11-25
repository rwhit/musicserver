- nprOne
  see ~/nprOne & additions to server.py
  - cache reco metadata
  - main screen should start auto-playing
  - pre-download recommendations (really need to build support for starting a download and playing before it completes)
    - read url & stream to both file & then (equiv of) tail -f  | mplayer
      This works:
        curl -s https://ondemand.npr.org/npr-mp6/npr/newscasts/2016/09/05/newscastShort090632.mp4 >/tmp/news.mp4 &
          (tail --pid $! -n +1 -f /tmp/news.mp4 | mplayer -)
      Or, try -cache option to mplayer? Any way to set interactively?
- have volume control everywhere
- have system volume control
  see amixer and alsactl
- "what's on" page to bring to current state
  generally better track current status so can come back later and even from diff device and get accurate:
  - what'splaying
  - status (paused vs playing)
  - position
  - volume
  - idea - use multiprocessing & queues and/or pipes
    one process just to track state - accepts both reads & writes
    a process that reads/parses mplayer output & sends update to state tracker
- for internet radio, pull ICY stream from mplayer output for what's currently playing
- another thought on full download of podcast w/out full delay - will mplayer work w/bash process substition?
  # start download w/curl
  # sleep a bit (or watch file size)
  # mplayer <(tail -n +1 -f $file)
  ** _downloadAndPlay does close enough - why doesn't that work? Is problem that we have to re-start it? Shouldn't be
  ** that big a deal
- for podcast, would be nice to re-start and go to a specific position rather than only beginning
* better way to get podcast w/no-delay: just pre-download them!
  + Create an (hourly say) cronjob
  + Set max space to use (and/or min free space on that disk)
  * Prioritize by age and rank
    by age done
  * expire by max age as well
  + update scheme to track what's available
  ? when listing podcasts, use union of cache + current feeds
- also see https://pypi.python.org/pypi/requests-cache
