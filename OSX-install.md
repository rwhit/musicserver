brew update
brew install pianobar
brew install mplayer
brew install libpq
sudo pip2 install flask flask-socketio requests eventlet psycopg2
initdb -D /usr/local/var/postgres
pg_ctl -D /usr/local/var/postgres start
##################
# in place of db/setup.sh
psql -d postgres -c "create role pi with login createdb;"
createdb pi
psql -U pi -f ./init.sql
##################
# subset of scripts/install.sh
HOME=/Users/rwhitworth/Documents/Personal/RaspPi
BASE=$HOME/musicserver/scripts
mkdir -p $HOME/mediaplayer
mkfifo $HOME/mediaplayer/fifo
sudo mkdir -p /var/run/musicserver
sudo chown pi /var/run/musicserver
# ...
sudo mkdir -p /data/musicserver/cache
sudo chown -R pi /data/musicserver
####################
# skipped, for now, wiring up pianobar
# update scripts/config, set MUSIC_BASE
##################
# create dummy secrets.py module
# why is this not doc'ed?