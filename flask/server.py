#!/usr/bin/env python

from flask import Flask, render_template, request, url_for, redirect
from flask_socketio import SocketIO, emit
from pianobarController import PianobarController
from podcastController import PodcastController
from radioController import RadioController
from subprocess import check_output, call
import logging
import sys
import os
import urllib
import requests
import psycopg2
import psycopg2.extras
import secrets as SECRETS
import time
import json

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secry'
socketio = SocketIO(app)
PORT = 80
HOST = '0.0.0.0'
PCONTROLLER = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pandora/")
def pandora():
    global PCONTROLLER
    if not PCONTROLLER:
        PCONTROLLER = PianobarController()
    else:
        PCONTROLLER.check_status()
    return render_template("pandora.html",
                data=PCONTROLLER.get_latest(),
                paused=PCONTROLLER.is_paused(),
                time=PCONTROLLER.get_time(),
                volume=PCONTROLLER.get_volume())

@socketio.on("volume", namespace="/pandorasocket")
def pandora_volume(volume):
    PCONTROLLER.set_volume(int(volume["data"]))
    broadcast_pandora("volumechanged", {"volume":PCONTROLLER.get_volume()})

@socketio.on("message", namespace="/pandorasocket")
def pandora_message(message):
    data = message["data"]
    PCONTROLLER.write(message["data"])
    if data == "p":
        PCONTROLLER.pause()
        broadcast_pandora("onpause", {"paused":PCONTROLLER.is_paused()})
    if PCONTROLLER.is_paused() and data[0:1] == "s":
        PCONTROLLER.pause()
        broadcast_pandora("onpause", {"paused":PCONTROLLER.is_paused()})
    return "OK"

@app.route("/pianobar/<action>", methods=["POST"])
def pianobar_message(action):
    data = request.json
    logging.debug("pianobar_message - action: {0} data: {1}".format(action, data))
    PCONTROLLER.set_latest(action, data)
    broadcast_pandora(action, data)
    return "OK"

def broadcast_pandora(action, data):
    socketio.emit(action, data, namespace="/pandorasocket")

PODCAST = None

def getPodcast():
    global PODCAST
    if not PODCAST:
        PODCAST = PodcastController()
    return PODCAST
    
@app.route("/podcast/")
def podcast():
    return render_template("podcast.html",
        feeds=getPodcast().get_feeds())

@app.route("/podcast/feed/<path:url>")
def podcast_feed(url):
    return render_template("podcast_feed.html",
        podcasts=getPodcast().get_feed(url))

@app.route("/podcast/play/<path:url>")
def podcast_play(url):
    return render_template("podcast_play.html",
        podcast=getPodcast().play_podcast(url,request.args.get('duration'), request.args.get('durationSecs'), request.args.get('title')),
        paused=False,
        time=getPodcast().get_time())

def broadcast_podcast(action, data):
    socketio.emit(action, data, namespace="/podcastsocket")

@socketio.on("message", namespace="/podcastsocket")
def podcast_message(message):
    data = message["data"].split('|')
    if data[0] == 'mp':
       getPodcast().write(data[1])
    elif data[0] == 'ct':
       if data[1] == 'next':
         getPodcast().playNext()
       elif data[1] == 'pause':
         getPodcast().pause()
         broadcast_podcast("onpause", {"paused":getPodcast().is_paused()})
       elif data[1] == 'swap':
         getPodcast().swap(data[2], data[3])
       else:
         logging.warn('Unknown podcastsocket message: ' + message)
    else:
      logging.warn('Unknown podcastsocket message: ' + message)
    return "OK"


RADIO = None

def getRadio():
    global RADIO
    if not RADIO:
        RADIO = RadioController()
    return RADIO

@app.route("/radio/")
def radio():
    radio = getRadio()
    return render_template("radio.html",
                data=radio.get_latest(),
                paused=radio.is_paused(),
                time=radio.get_time(),
                volume=radio.get_volume())

def broadcast_radio(action, data):
    socketio.emit(action, data, namespace="/radiosocket")

@socketio.on("message", namespace="/radiosocket")
def radio_message(message):
    data = message["data"].split('|')
    if data[0] == 's':
       getRadio().play(data[1],data[2])
    elif data[0] == 'pause':
       getRadio().pause()
       broadcast_radio("onpause", {"paused":getRadio().is_paused()})
    else:
         logging.warn('Unknown radiosocket message: ' + mesage)
    return "OK"

NPR_STATE_NEED_AUTH=0
NPR_STATE_NEED_TOKEN=1
NPR_STATE_AUTHORIZED=2

SCHEME_AND_HOST = 'http://rasp-music'
@app.route("/nprOne")
def nprOne():
  # see nprOne/flow.txt
  state=getNprState(request)
  logging.info("nprOne - state is {}".format(state))
  if(state == NPR_STATE_NEED_AUTH):
    logging.info("nprOne - redirecting for OAuth")
    # 1. no cookie - set cookie, RM=state:AUTH; (can you do that? seems like yes, modulo browser bugs) and redirect to auth, include state=<csrf-token>
    # https://api.npr.org/authorization/v2/authorize?client_id=%(client_id)s&redirect_uri=http%3A%2F%2Frasp-music%2FnprOne&response_type=code&scope=identity.readonly%20identity.write%20listening.readonly%20listening.write&state=abc123
    params={
      'client_id': SECRETS.clientId,
      'redirect_uri': urllib.quote(SCHEME_AND_HOST + url_for('nprOne'),''),
      'scopes': urllib.quote('identity.readonly identity.write listening.readonly listening.write localactivation',''),
      'csrfToken': urllib.quote(generateCsrf(request, SECRETS.csrfKey))
    }
    
    location='https://api.npr.org/authorization/v2/authorize?client_id=%(client_id)s&redirect_uri=%(redirect_uri)s&response_type=code&scope=%(scopes)s&state=%(csrfToken)s' % params
    return redirect(location, code=302)
  if(state == NPR_STATE_NEED_TOKEN):
    logging.info("nprOne - got code, getting token")
    #curl -X POST --header 'Content-Type: application/x-www-form-urlencoded' \
    #  --header 'Accept: application/json' \
    #  -d 'grant_type=authorization_code&client_id=%(client_id)s&client_secret=%(client_secret)s&code=%(code)s&redirect_uri=http%3A%2F%2Frasp-music%2FnprOne' \
    #  'https://api.npr.org/authorization/v2/token'
    params={
      'grant_type':    'authorization_code',
      'client_id' :    SECRETS.clientId,
      'client_secret': SECRETS.clientSecret,
      'redirect_uri':  SCHEME_AND_HOST + url_for('nprOne'),
      'code':          request.args.get('code'),
    }
    # doesn't work. complains about grant_type, but I think it only support  form urlencoded, not json
    #tokenResp = requests.post('https://api.npr.org/authorization/v2/token', json=params, headers = {'Accept': 'application/json'})
    # works:
    tokenResp = requests.post('https://api.npr.org/authorization/v2/token', data=params, headers = {'Accept': 'application/json'})
    if(tokenResp.status_code != 200):
      logging.info("nprOne - token request failed - status is {}, body is {}".format(tokenResp.status_code, tokenResp.text))
      outParams = { 'status': tokenResp.status_code, 'body': tokenResp.text , 'reqHeaders': str(tokenResp.request.headers), 'reqBody': tokenResp.request.body }
      return 'requested token, status = %(status)d, body = %(body)s requestHeaders = %(reqHeaders)s requestBody = %(reqBody)s' % outParams

    # store our token
    logging.info("nprOne - token request succeeded, getting recommendations")
    json = tokenResp.json()
    accessToken = json.get('token_type') + ' ' + json.get('access_token')
    validSeconds = json.get('expires_in')
    storeNprToken(accessToken, validSeconds)

    return getNprRecommendations(accessToken)

  if(state == NPR_STATE_AUTHORIZED):
    logging.info("nprOne - authorized, getting recommendations")
    (token, expires) = getNprToken()
    return getNprRecommendations(token)

def getNprRecommendations(accessToken):
    # now get recommendations
    headers = {
      'Authorization': accessToken,
      'Accept':        'application/json',
      'X-Advertising-ID': SECRETS.advertisingId,
    }
    recoResp = requests.get('https://api.npr.org/listening/v2/recommendations?channel=npr', headers = headers)
    fname='/tmp/npr-reco.json'
    itemList = json.loads(recoResp.text)
    jsonPretty = json.dumps(itemList,indent=2)
    with open(fname,'w') as fd:
      fd.write(jsonPretty)
    outParams = { 'status': recoResp.status_code,
                  'note': 'dumped json to {}'.format(fname),
                  'body': jsonPretty,
                  'reqHeaders': str(recoResp.request.headers),
                  'reqBody': recoResp.request.body }
    #return 'recommendations: (status = %(status)d)<br/>note: %(note)s<br/></br><pre>%(body)s</pre>' % outParams
    # pull out just the data we want:
    # for item in itemList['items']
    #  Title - item['attributes']['title']
    #  preferred url (audio/aac, audio/mp3)
    #    for audioLink in item['links']['audio']
    #      audioLink['href'], audioLink['content-type']
    #  preferred image (icon, logo)
    #    for imgLink in item['links']['audio']
    #      imgLink['href'], imgLink['rel']
    #  traceback info
    #  - see   http://dev.npr.org/guide/app-experience/core-reqs/sponsorship/
    #      and http://dev.npr.org/guide/services/listening/#Ratings
    #    rating object is item['rating']
    #      POST back to item['links']['recommendations'][0]['href'] with updated 'rating' and 'timestamp'
    #        START on start & every 5 minutes during playback
    recommendations=[]
    for item in itemList['items']:
        reco={}
        recommendations.append(reco)
        pref=100
        for audioLink in item['links']['audio']:
            newPref=getNprAudioPref(audioLink)
            if newPref < pref:
                pref = newPref
                audioUrl = audioLink['href']
        pref=100
        if 'image' in item['links']:
            for imgLink in item['links']['image']:
                newPref=getNprImagePref(imgLink)
                if newPref < pref:
                    pref = newPref
                    imgUrl = imgLink['href']
            reco['imgUrl']   = imgUrl
        reco['audioUrl'] = audioUrl
        reco['title']    = item['attributes']['title']
    return render_template('nprOne.html', recommendations=recommendations)

# lower is better
CTYPE_TO_PREF_MAP = {
    'audio/aac' : 1,
    'audio/mp3' : 2,
}

def getNprAudioPref(audioLink):
    ctype = audioLink['content-type']
    if(ctype in CTYPE_TO_PREF_MAP): return CTYPE_TO_PREF_MAP[ctype]
    return 99

# lower is better
REL_TO_PREF_MAP = {
    'icon' : 1,
    'logo' : 2,
    'logo_square': 3,
}

def getNprImagePref(imgLink):
    rel = imgLink['rel']
    if(rel in REL_TO_PREF_MAP): return REL_TO_PREF_MAP[rel]
    return 99

NPR_STATE_DBNAMESPACE = 'nprOne'
NPR_STATE_DBKEY='state'
def getNprState(request):
    # see if we have a valid token
    if(haveValidNprToken()):
      return NPR_STATE_AUTHORIZED
    if(request.args.get('code')):
      return NPR_STATE_NEED_TOKEN
    return NPR_STATE_NEED_AUTH

# nprState schema
# { "token": { "value": "<value>",
#               "expires": <seconds since epoch>, },
# }

def haveValidNprToken():
    (token, expires) = getNprToken()
    if(not token):
        return False
    if(not expires or expires < time.time()):
        return False
    return True

def getNprToken():
    tokenValue = False
    expires = False
    conn = psycopg2.connect('dbname=pi user=pi')
    psycopg2.extras.register_json(conn)
    try:
        with conn.cursor() as cursor:
            cursor.execute('select value from app_state where namespace = %(namespace)s and key = %(key)s',
                           {'namespace': NPR_STATE_DBNAMESPACE, 'key':NPR_STATE_DBKEY})
            nprState = cursor.fetchone()
            if(not nprState):
                return (False, False)
            token = nprState[0]['token']
            tokenValue = token['value']
            expires = token['expires']
    finally:
        conn.close()
    return (tokenValue, expires)

def storeNprToken(value, validSeconds):
    conn = psycopg2.connect('dbname=pi user=pi')
    psycopg2.extras.register_json(conn)
    state = { 'token':
              { 'value': value, 'expires': time.time() + validSeconds },
            }
    try:
        with conn.cursor() as cursor:
            cursor.execute('delete from app_state where namespace = %(namespace)s and key = %(key)s',
                           {'namespace': NPR_STATE_DBNAMESPACE, 'key':NPR_STATE_DBKEY})
            valueJson = psycopg2.extras.Json(state)
            logging.debug("valueJson: " + valueJson.getquoted())
            cursor.execute('insert into app_state (namespace, key, value) values(%(namespace)s, %(key)s, %(value)s)',
                           {'namespace': NPR_STATE_DBNAMESPACE, 'key':NPR_STATE_DBKEY, 'value': valueJson})
            conn.commit()
    finally:
        conn.close()
    
def generateCsrf(request, key):
  # TODO implement for reals
  return 'abc123'

@app.route("/admin")
def admin():
   return render_template("admin.html")

def broadcast_admin(action, data):
    socketio.emit(action, data, namespace="/adminsocket")

# message: action
#     restart - restart server
@socketio.on("message", namespace="/adminsocket")
def admin_message(message):
   action=message["data"]
   logging.debug("/admin, action is " + str(action))
   if(action == 'restart'):
     logging.warn("Restarting server")
     try:
       with open(os.devnull,'r') as devNull:
         output="/tmp/restart.out"
         result=call(['( sleep 1;../scripts/musicserver >' + output + ' 2>&1 ) &'], shell=True, stdin=devNull, close_fds=True)
     except:
       result="Exception: " + str(sys.exc_info())
   logging.debug("admin result" + str(result))
   broadcast_admin("adminResult", {"result":"restarting server - " + str(result)})
   return "OK"

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.info('starting server')
    # disable flash policy server
    socketio.run(app, port=PORT, host=HOST)
    broadcast_admin("adminResult", {"result":"server restarted"})
