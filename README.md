musicserver
===========

Quick flask based music server for use on a rasberry pi

#Dependencies
    apt-get update
    apt-get install build-essential libao-dev libmad0-dev libfaad-dev libgnutls-dev libjson0-dev git libgcrypt11-dev yasm make pkg-config python-dev mplayer postgresql libpq-dev libcap2-bin lsof
##Install ffmpeg from source
    git clone https://github.com/FFmpeg/FFmpeg.git
    cd FFmpeg
    ./configure
    # 'make' can take several hours
    make clean && make && make install
    cd ..
## install pianobar manually from source
    git clone https://github.com/PromyLOPh/pianobar.git
    cd pianobar
    make clean && make && make install
## configure alsa
    vim /usr/share/alsa/alsa.conf
    # pcm.front cards.pcm.front => pcm.front cards.pcm.default
# Python dependencies
    # download get-pip.py
    ./get-pip.py
    pip install flask flask-socketio requests eventlet psycopg2
# Allow python to bind to port 80 (if non-root user)
    sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python))
# Setup db schema
    cd db
    sudo -u postgres psql -f ./init.sql
# Start server
    cd flask
    chmod a+x server.py
    ./server.py

# websocket io library from https://cdn.socket.io/socket.io-1.4.5.js
