+ bought rasp-music.info from namecheap
+ setting up for letsencrypt
  X certbot failed - really old version
    sudo apt-get install certbot
    certbot -d *.rasp-music.info --manual --preferred-challenges dns certonly
  + acme.sh
    cd ~
    git clone https://github.com/Neilpang/acme.sh.git
    cd ./acme.sh/
    ./acme.sh --install
    acme.sh --issue --dns -d *.rasp-music.info -d rasp-music.info --yes-I-know-dns-manual-mode-enough-go-ahead-please
    # setup 2 TXT records
    # verify
    dig _acme-challenge.rasp-music.info txt
    # retrieve cert
    acme.sh --renew --dns -d *.rasp-music.info -d rasp-music.info --yes-I-know-dns-manual-mode-enough-go-ahead-please
    # --install added a cronjob. Since I can't automate this process yet, commented that out via crontab -e
    # NOTE for automation to work, need api key, but namecheap doesn't give those out for small accounts
- setup flask to use it
  http://flask.pocoo.org/snippets/111/

