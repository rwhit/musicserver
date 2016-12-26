#!/bin/bash
crontab <<EOF
# restart musicserver just after 3am, rolls logs
05 03 * * * /home/pi/musicserver/scripts/musicserver >/tmp/musicserver.out 2>&1
EOF
