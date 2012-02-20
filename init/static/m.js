function format_filters(d) {
        fset_id = d[0]
        s = ""
	if (fset_id == 0) {
		selected = "selected"
	} else {
		selected = ""
	}
	s += "<option value=0 "+selected+">none</option>"
        for (id in d[1]) {
                data = d[1][id]
                if (data['id'] == fset_id) {
                        selected = "selected"
                } else {
                        selected = ""
                }
                s += "<option value="+data['id']+" "+selected+">"+data['fset_name']+"</option>"
        }
        return s
}

function init_filters(event, data) {
        $.getJSON("{{=URL(r=request, f='call/json/json_filters')}}", function(data) {
                e = format_filters(data)
                $("#filters").append(e).selectmenu('refresh')
        });
        $('#filters').change('select', select_filter)
}

function select_filter(event, data) {
        $.getJSON("{{=URL(r=request, f='call/json/json_set_filter')}}/"+$(this).attr('value'), function(data) {
		location.reload()
        });
}

function format_service(data) {
	s = ""
	for (i=0; i<data.length; i++) {
		s += "<li><a rel='external' href='{{=URL(r=request, f='svc')}}/"+data[i]+"'>" + data[i] + "</a></li>"
	}
        return s
}

function format_node(data) {
	s = ""
	for (i=0; i<data.length; i++) {
		s += "<li><a rel='external' href='{{=URL(r=request, f='node')}}/"+data[i]+"'>" + data[i] + "</a></li>"
	}
        return s
}

