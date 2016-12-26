volumeDate = new Date();
function sendMessage(/*string*/ message) {
    socket.emit("message", {data: message});
}
function onAdminResult(data) {
    if(data["result"]) {
        $("#result").text(data["result"])
        $("#result").removeClass("hidden");
    }
}
function initHandlers() {
    socket.on('adminResult', onAdminResult);
}
