musicserver
===========

Quick flask based music server for use on a rasberry pi

#Dependencies
    apt-get update
    apt-get install build-essential libao-dev libmad0-dev libfaad-dev libgnutls-dev libjson0-dev git libgcrypt11-dev yasm make pkg-config python-dev mplayer postgresql libpq-dev libcap2-bin
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
    readlink -f `which python`
    sudo setcap 'cap_net_bind_service=+ep' /path/to/python
# install json_91 (back port of json support) from source
    # need pg dev package to build extensions
    sudo apg-get install postgresql-server-dev-9.1
    # get the extension source, then build it
    git clone https://bitbucket.org/adunstan/json_91.git
    cd json_91
    make
    sudo make install
    # get around os/pg permissions issues
    touch regression.out regression.diffs
    chmod 777 regression.out regression.diffs results
    sudo -u postgres make installcheck
  
    # add it to our db
    sudo -u postgres psql -U postgres -d pi -c 'create extension json;'
# Setup db schema
    cd db
    psql -f ./init.sql
# Start server
    cd flask
    chmod a+x server.py
    ./server.py

