volumeDate = new Date();
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
var musicTimer = new (function() {
    var slider,
        incrementVal = 500, //How often to update timer in ms
        currentVal = 0,
        starVal,
        autoStart,
    updateTimer = function() {
        var val;
        currentVal += incrementVal/1000;
        slider.val(currentVal);
        val = slider.val() / (slider.attr('max') - 0);
        slider.css('background-image',
                '-webkit-gradient(linear, left top, right top, '
                + 'color-stop(' + val + ', #005050), '
                + 'color-stop(' + val + ', #006f6f)'
                + ')'
                );
    },
    init = function() {
        slider = $("#timerSlider");
        musicTimer.Timer = $.timer(updateTimer, incrementVal, false);
    };
    this.setup = function(startvalue, maxvalue) {
        currentVal = startvalue;
        slider.val(startvalue);
        slider.attr('max', maxvalue)
    };
    $(init);
});
