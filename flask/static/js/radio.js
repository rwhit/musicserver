volumeDate = new Date();
function sendMessage(/*string*/ message) {
    socket.emit("message", {data: message});
}
function toggleStations() {
    $("#stations").toggleClass("hidden");
}
function volumeChanged(/*event*/ event) {
    var slider = document.getElementById('volumeSlider');
    socket.emit("volume", {data: slider.value});
    volumeDate = new Date();
}
function setStationInfo(/* json */ data, /*bool*/ paused, /*int*/ time) {
    if(!data) {
        return;
    }
    if(!paused) {
        paused = "";
    }
    if(!time) {
        time = 0;
    }
    //Color thumbs up
    if(parseInt(data["rating"]) == 1) {
        $("#up").hide();
    } else {
        $("#up").show();
    }
    //Set station info
//    $("#stationImage").attr("src",data["stationImage"]);
    //Set songName, artist and albumName
    $("#stationName").html(data["stationName"]);
    //Set stations
    setStations(data);
}
function setStations(/* json */data) {
    var selector = $("#stations");
    var needSelect = true;
    selector.html("");
    var stationList = $("<ul>");
    var curStation = data["current_station"];
    selector.append(stationList);
    stations = data["stations"];
    var numStations = stations.length;
    for(var i = 0; i<numStations; i++) {
        var selected = "";
        if(stations[i][0] == curStation) {
            selected = "selected='true'"
        }
        stationList.append("<li onclick='sendMessage(\"s|"+stations[i][1] +"|"+ stations[i][0]+"\\n\");'>" + stations[i][0] + "</li>");
    }
    $("#selectedStation").html(curStation.substring(0,curStation.length-1));
}
function onPause(data) {
    if(data["paused"]) {
        $("#play").removeClass("hidden");
        $("#pause").addClass("hidden");
        musicTimer.Timer.pause();
    } else {
        $("#play").addClass("hidden");
        $("#pause").removeClass("hidden");
        musicTimer.Timer.play();
    }
}
function onVolumeChange(data) {
    if((new Date() - volumeDate) > 3000) {
        //Someone else changed the volume
        $("#volumeSlider").val(parseInt(data["volume"]));
    }
}
function onUserGetStations(data) {
    setStations(data);
}
function initHandlers() {
    socket.on('onpause', onPause);
    socket.on('volumechanged', onVolumeChange);
    socket.on('usergetstations', onUserGetStations);
}
var radioController = new ( function() {
    this.thumbsUp = function() {
      // no-op for now
    },
    this.thumbsDown = function() {
      // no-op for now
    },
    this.playOrPause = function() {
      sendMessage('pause');
    },
    this.next = function() {
      sendMessage('next');
    };
});
