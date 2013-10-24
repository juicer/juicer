function juicer_hello(){
    var $t = $('#juicer-hello-output');

    $("#juicer-hello-overlay").css({
	opacity : 0.5,
	top     : $t.offset().top,
	width   : $t.outerWidth(),
	height  : $t.outerHeight()
    });

    $("#img-load").css({
	top  : (($t.height() / 2) + 16),
	left : ($t.width() / 2)
    });

    $("#juicer-hello-overlay").fadeIn();
    $.getJSON("/rest/juicer/hello", function(data) {
	$.each(data, function(env, response) {
	    $('#juicer-hello-output').append("<b>" + env + "</b><br />");
	    $('#juicer-hello-output').append(JSON.stringify(response));
	    $('#juicer-hello-output').append("<br />");
	});
	$("#juicer-hello-overlay").fadeOut();
    });
}


$(document).ready(function(){
    $('#button-juicer-hello').click(function () {
	console.log("Hello clicked");
        juicer_hello();
    });
});
