function juicer_list($filter){
    $('#list-carts option').remove();
    $.getJSON("/rest/juicer/list/*" + $filter + "*", function(data) {
	$.each(data, function(i, cart) {
	    $("#list-carts").append("<option value='" + cart + "'>" + cart + "</option>");
	});
    });
}

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
    // Load carts by default
    juicer_list('*');

    $('#button-juicer-hello').click(function () {
	console.log("Hello clicked");
        juicer_hello();
    });

    $("#input-juicer-list").on("input", null, null, juicer_list_filter);
});

function juicer_list_filter() {
    var $list_filter = $('#input-juicer-list').val();
    juicer_list($list_filter);
}