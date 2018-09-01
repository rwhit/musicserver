#!/bin/bash
HOME=/home/pi
BASE=$HOME/musicserver/scripts
mkdir -p $HOME/mediaplayer
mkfifo $HOME/mediaplayer/fifo
sudo mkdir -p /var/run/musicserver
sudo chown pi:pi /var/run/musicserver
sudo cp $BASE/musicserver.conf /usr/lib/tmpfiles.d/
$BASE/crontab.sh
sudo ln -s $BASE/init/musicserver /etc/init.d
sudo update-rc.d musicserver defaults
sudo service musicserver start
sudo mkdir -p /data/musicserver/cache
sudo chown -R pi:pi /data/musicserver
echo "Need to setup pianobar config - see configcopy dir & getPandoraTlsFingerprint.sh"
