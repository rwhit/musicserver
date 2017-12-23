musicserver
===========

Quick flask based music server for use on a rasberry pi

#Dependencies
    apt-get update
    sudo apt-get install build-essential libao-dev libmad0-dev libfaad-dev  git libgcrypt11-dev yasm make pkg-config python-dev mplayer postgresql libpq-dev libcap2-bin autoconf libcurl4-gnutls-dev lsof pianobar
## wire pianobar to flask
    # see configcopy dir & note in scripts/install.sh - why not doc'ed?!
## configure alsa
    vim /usr/share/alsa/alsa.conf
    # pcm.front cards.pcm.front => pcm.front cards.pcm.default
# Python dependencies
    sudo apt-get install python3-pip
    sudo pip3 install flask flask-socketio requests eventlet psycopg2
# Allow python to bind to port 80 (if non-root user)
    sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))
# Setup db schema
    cd db
    ./setup.sh
# install crontab & service, Start server
    cd scripts
    ./install.sh

# websocket io library from https://cdn.socket.io/socket.io-1.4.5.js

