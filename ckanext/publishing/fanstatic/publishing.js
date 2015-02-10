$( document ).ready(function() {
	$('form').bind('submit', function() {
        $(this).find(':input').removeAttr('disabled');
    });
	
	$( "#authorization_required" ).change(function () {
	    checked = $( "#authorization_required" ).prop('checked');
	    if(checked) {
	    	$("#authorization").removeAttr('disabled');
	    } else {
	    	$("#authorization").attr('disabled','disabled');
	    }
	  });
	
	$( "#authorization_required" ).change();
});
