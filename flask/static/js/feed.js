function initHandlers() {
}
function sendMessage(/*string*/ message) {
    socket.emit("message", {data: message});
}
function moveUp(event) {
  event.stopPropagation();
  var $current = $(event.target).closest('li');
  var $previous = $current.prev('li');
  if($previous.length !== 0){
    $current.insertBefore($previous);
    sendMessage('ct|swap|' + $current.data("url") + "|" + $previous.data("url"));
  }
  return false;
}
function moveDown(event) {
  event.stopPropagation();
  var $current = $(event.target).closest('li');
  var $next = $current.next('li');
  if($next.length !== 0){
    $current.insertAfter($next);
    sendMessage('ct|swap|' + $current.data("url") + "|" + $next.data("url"));
  }
  return false;
}
