function sendMessage(/*string*/ message) {
    socket.emit("message", {data: message});
}
function setPodcastInfo(/*json*/podcast, /*bool*/paused, /*int*/time) {
    musicTimer.setup(time,parseInt(podcast["durationSecs"]));
    if(paused != 'True') {
      musicTimer.Timer.play();
    }
}
function initHandlers() {
//    socket.on('songstart', setSongInfo);
//    socket.on('songlove', function() { $("#up").hide(); });
    socket.on('onpause', onPause);
//    socket.on('volumechanged', onVolumeChange);
//    socket.on('usergetstations', onUserGetStations);
}
var podcastController = new ( function() {
    this.thumbsUp = function() {
      // no-op for now
    },
    this.thumbsDown = function() {
      // no-op for now
    },
    this.playOrPause = function() {
      sendMessage('ct|pause');
    },
    this.next = function() {
      sendMessage('ct|next');
    };
});
