#!/bin/bash
home=$(dirname $0)
source $home/config
LOGS=${MUSIC_BASE}/flask/logs
crontab <<EOF
# restart musicserver just after 3am, rolls logs
05 03 * * * /home/pi/musicserver/scripts/musicserver --init /var/run/musicserver.pid >${LOGS}/restart-musicserver.out 2>&1
# hourly pre fetch podcasts
28 * * * * flock --exclusive --nonblock /var/run/musicserver/PREFETCH_LOCK /home/pi/musicserver/scripts/prefetch.py >>${LOGS}/pre_fetch.out 2>&1
EOF
sudo crontab <<EOF
# remount dobby just before the hourly prefetch
26 * * * * mount /data/dobby
EOF
