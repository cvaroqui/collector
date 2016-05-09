function tags(options) {
	var o = {}
	o.options = options

	try {
		// element id
		o.div = $("#"+options.tid)
	} catch(e) {
		// jquery object
		o.div = options.tid
		o.div.uniqueId()
		o.options.tid = o.div.attr("id")
	}
	o.div.css({"min-height": "1em"})

	o.load = function() {
		// init error display zone
		if (!o.div.info) {
			info = $("<div></div>")
			o.div.append(info)
			o.div.info = info
		}
		o.div.info.empty()
		spinner_add(o.div.info)
		o.get(o.options.prefix, function(_data) {
			spinner_del(o.div.info)
			if (_data.error) {
				o.div.info.html(services_error_fmt(_data))
				return
			}
			_data = _data.data
			if ((_data.length == 0) && o.options.candidates) {
				if (o.options.create) {
					var msg = "tags.no_candidates_create"
				} else {
					var msg = "tags.no_candidates"
				}
				o.div.info.text(i18n.t(msg))
			}
			d = $("<div name='tag_container'></div>")
			for (i=0; i<_data.length; i++) {
				d.append(o.add_tag(_data[i]), " ")
			}
			if (o.options.responsible && o.options.candidates != true) {
				d.append(o.add_add_tag())
				d.append(o.add_del_tag())
			}
			o.div.find("[name=tag_container]").remove()
			o.div.prepend(d)

			o.bind_admin_tools()
		},
		function(xhr, stat, error) {
			o.div.info.html(services_ajax_error_fmt(xhr, stat, error))
		})
	}

	o.add_tag = function(tag_data) {
		if (o.options.candidates == true) {
			cl = "icon tag tag_candidate"
		} else {
			cl = "icon tag tag_attached"
		}
		s = "<span tag_id='"+tag_data.id+"' class='"+cl+"'>"+tag_data[o.options.tag_name]+" </span>"
		e = $(s)
		e.bind("mouseover", function(){
			if (o.options.responsible && o.options.candidates != true) {
				$(this).addClass("tag_drag")
			}
		})
		e.bind("mouseout", function(){
			if (o.options.responsible && o.options.candidates != true) {
				$(this).removeClass("tag_drag")
			}
		})
		e.bind("click", function(event){
			event.stopPropagation()
			if (!o.options.responsible) {
				return
			}
			if ($(this).hasClass("tag_candidate")) {
				o.attach_tag(tag_data)
				return
			}
		})
		e.draggable({
			"containment": o.div,
			"opacity": 0.9,
			"revert": true,
			"stack": ".tag",
		})
		return e
	}

	o.del_tag = function(tag_data) {
		o.div.find("[tag_id="+tag_data.tag_id+"].tag").hide("fade", function(){
			$(this).remove()
		})
	}

	o.add_add_tag = function() {
		if (o.options.candidates) {
			return
		}
		e = $("<span class='icon tag_add'></span>")
		e.css({"display": "none"})
		e.text(i18n.t("tags.add"))
		e.bind("click", function(){
			old_html = $(this).html()
			e = $(this).find(".tag_input")
			if (e.length>0) {
				return
			}
			s = "<input class='tag_input'></input>"
			$(this).html(s)
			e = $(this).find(".tag_input")
			e.bind("keyup", function(event){
				tag = $(this).parent()
				tag_name = $(this).val()
				o.input_keyup(event, tag, tag_name)
			})
			e.focus()
		})
		return e
	}

	o.add_del_tag = function() {
		if (o.options.candidates) {
			return
		}
		e = $("<span class='icon tag_del'></span>")
		e.css({"display": "none"})
		e.text(i18n.t("tags.del"))
		e.droppable({
			accept: ".tag",
			activeClass: "tag_del_active",
			hoverClass: "tag_del_hover",
			drop: function(event, ui) {
				o.detach_tag(ui.draggable)
			}
		})
		return e
	}

	o.add_candidates = function(tag, tag_name) {
		prefix = o.div.find(".tag_input").val()
		if (prefix.length == 0) {
			prefix = "%"
		}
		prefix = prefix.replace(/\//, "_")
		prefix = encodeURIComponent(prefix)

		// 1st candidates exec: init a new tag object
		ctid = o.options.tid+"c"
		options = $.extend({}, o.options, {
			"tid": ctid,
			"parent_object": o,
			"prefix": prefix,
			"candidates": true
		})
		o.div.find("#"+ctid).parent().remove()
		e = $("<span><h3>"+i18n.t("tags.candidates")+"</h3><div id='"+ctid+"' class='tags'></div></span>")
		o.div.append(e)
		o.candidates = tags(options)
	}

	o._attach_tag = function(tag_data) {
		o.div.info.empty()
		spinner_add(o.div.info, i18n.t("tags.attaching"))
		o.options.attach(tag_data, function(jd) {
			spinner_del(o.div.info)
			if (jd.error) {
				o.div.info.html(services_error_fmt(jd))
				return
			}
			// refresh tags
			if (o.options.parent_object) {
				o.div.parent().remove()
				o.options.parent_object.load()
			} else {
				o.load()
			}
		},
		function(xhr, stat, error) {
			o.div.info.html(services_ajax_error_fmt(xhr, stat, error))
		})
	}

	o.create_and_attach_tag = function(tag_data) {
		o.div.info.empty()
		o.candidates.div.parent().remove()
		o.options.get_candidates(tag_data.tag_name, function(jd) {
			if (!jd.data || (jd.data.length == 0)) {
				// tag does not exist yet ... create
				spinner_add(o.div.info, i18n.t("tags.creating"))
				o.options.create(tag_data, function(jd) {
					spinner_del(o.div.info)
					if (jd.error) {
						o.div.info.html(services_error_fmt(jd))
						return
					}
					o._attach_tag(jd.data)
				},
				function(xhr, stat, error) {
					o.div.info.html(services_ajax_error_fmt(xhr, stat, error))
				})
			} else {
				// tag elready exists
				o._attach_tag(jd.data[0])
			}
		},
		function(xhr, stat, error) {
			o.div.info.html(services_ajax_error_fmt(xhr, stat, error))
		})
	}

	o.attach_tag = function(tag_data) {
		if (!tag_data.id) {
			// from <enter> in add tag
			o.create_and_attach_tag(tag_data)

		} else {
			// from click on a candidate
			o._attach_tag(tag_data)
		}
	}

	o.detach_tag = function(tag) {
		o.div.info.empty()
		tag.hide()
		spinner_add(o.div.info, i18n.t("tags.detaching"))
		o.options.detach(tag, function(jd) {
			spinner_del(o.div.info)
			if (jd.error) {
				o.div.info.html(services_error_fmt(jd))
				return
			}
			// refresh tags
			o.load()
		},
		function(xhr, stat, error) {
			tag.show()
			o.div.info.html(services_ajax_error_fmt(xhr, stat, error))
		})
	}

	o.bind_admin_tools = function() {
		// show tag admin tools to responsibles and managers
		if (o.options.responsible) {
			o._bind_admin_tools()
			return
		}
		if (services_ismemberof("Manager")) {
			o._bind_admin_tools()
		}
	}
	o._bind_admin_tools = function() {
		o.div.hover(
			function(){
				o.div.find(".tag_add,.tag_del").show()
			},
			function(){
				o.div.find(".tag_add,.tag_del").hide()
			}
		)
	}

	o.event_handler = function(data) {
		if (o.options.candidates == true) {
			return
		}
		if (!("data" in data)) {
			return
		} 
		data = data.data
		if (o.options.node_id) {
			if (!data.node_id || (o.options.node_id != data.node_id)) {
				return
			}
		} else if (o.options.svc_id) {
			if (!data.svc_id || (o.options.svc_id != data.svc_id)) {
				return
			}
		}
		if (!("action" in data)) {
			return
		}
		if (data["action"] == "attach") {
			if (o.div.find("[tag_id="+data.tag_id+"]").length > 0) {
				return
			}
			o.div.children("div").first().prepend(o.add_tag({
				"id": data.tag_id,
				"tag_name": data[o.options.tag_name]
			}))
		} else if (data.action == "detach") {
			o.del_tag({
				"tag_id": data.tag_id,
			})
		}
	}

	o.input_keyup = function(event, tag, tag_name) {
		if (!is_enter(event)) {
			tag.removeClass("tag_create")
			tag.find("input").removeClass("tag_create")
			o.add_candidates(tag, tag_name)
			return
		}
		o.attach_tag({"tag_name": tag_name})
	}

	o.get = function(prefix, callback, callback_err) {
		if ("candidates" in o.options) {
			return o.options.get_candidates(prefix, callback, callback_err)
		} else {
			return o.options.get_tags(prefix, callback, callback_err)
		}
	}

	wsh["tags_"+o.options.tid] = function(data) {
		o.event_handler(data)
	}

	o.options.am_i_responsible(function(jd){
		o.options.responsible = jd.data
		o.load()
	})
	return o
}

function node_tags(options) {
	options.tag_name = "tag_name"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("R_NODE_TAGS", [options.node_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("R_NODE_CANDIDATE_TAGS", [options.node_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": [options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.create = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_TAGS", "", "", tag_data, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_TAG_NODE", [tag_data.id, options.node_id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_TAG_NODE", [tag.attr("tag_id"), options.node_id], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_NODE_AM_I_RESPONSIBLE", [options.node_id], "", callback)
	}
	return tags(options)
}

function service_tags(options) {
	options.tag_name = "tag_name"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("R_SERVICE_TAGS", [options.svc_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("R_SERVICE_CANDIDATE_TAGS", [options.svc_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": [options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.create = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_TAGS", "", "", tag_data, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_TAG_SERVICE", [tag_data.id, options.svc_id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_TAG_SERVICE", [tag.attr("tag_id"), options.svc_id], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_SERVICE_AM_I_RESPONSIBLE", [options.svc_id], "", callback)
	}
	return tags(options)
}

function app_responsibles(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/apps/%1/responsibles", [options.app_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_APP_RESPONSIBLE", [options.app_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_APP_RESPONSIBLE", [options.app_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_APP_AM_I_RESPONSIBLE", [options.app_id], "", callback)
	}
	return tags(options)
}

function app_publications(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/apps/%1/publications", [options.app_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_APP_PUBLICATION", [options.app_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_APP_PUBLICATION", [options.app_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_APP_AM_I_RESPONSIBLE", [options.app_id], "", callback)
	}
	return tags(options)
}

function form_responsibles(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/forms/%1/responsibles", [options.form_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_FORM_RESPONSIBLE", [options.form_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_FORM_RESPONSIBLE", [options.form_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_FORM_AM_I_RESPONSIBLE", [options.form_id], "", callback)
	}
	return tags(options)
}

function form_publications(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/forms/%1/publications", [options.form_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("R_FORM_PUBLICATION", [options.form_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("R_FORM_PUBLICATION", [options.form_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("R_FORM_AM_I_RESPONSIBLE", [options.form_id], "", callback)
	}
	return tags(options)
}

function ruleset_responsibles(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/compliance/rulesets/%1/responsibles", [options.ruleset_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("/compliance/rulesets/%1/responsibles/%2", [options.ruleset_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("/compliance/rulesets/%1/responsibles/%2", [options.ruleset_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("/compliance/rulesets/%1/am_i_responsible", [options.ruleset_id], "", callback)
	}
	return tags(options)
}

function ruleset_publications(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/compliance/rulesets/%1/publications", [options.ruleset_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("/compliance/rulesets/%1/publications/%2", [options.ruleset_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("/compliance/rulesets/%1/publications/%2", [options.ruleset_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("/compliance/rulesets/%1/am_i_responsible", [options.ruleset_id], "", callback)
	}
	return tags(options)
}

function modset_responsibles(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/compliance/modulesets/%1/responsibles", [options.modset_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("/compliance/modulesets/%1/responsibles/%2", [options.modset_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("/compliance/modulesets/%1/responsibles/%2", [options.modset_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("/compliance/modulesets/%1/am_i_responsible", [options.modset_id], "", callback)
	}
	return tags(options)
}

function modset_publications(options) {
	options.tag_name = "role"
	options.get_tags = function(prefix, callback, callback_err) {
		services_osvcgetrest("/compliance/modulesets/%1/publications", [options.modset_id], {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false"
		}, callback, callback_err)
	}
	options.get_candidates = function(prefix, callback, callback_err) {
		services_osvcgetrest("/groups", "", {
			"props": "id," + options.tag_name,
			"limit": "0",
			"meta": "false",
			"filters": ["privilege F", options.tag_name+" "+prefix+"%"]
		}, callback, callback_err)
	}
	options.attach = function(tag_data, callback, callback_err) {
		services_osvcpostrest("/compliance/modulesets/%1/publications/%2", [options.modset_id, tag_data.id], "", "", callback, callback_err)
	}
	options.detach = function(tag, callback, callback_err) {
		services_osvcdeleterest("/compliance/modulesets/%1/publications/%2", [options.modset_id, tag.attr("tag_id")], "", "", callback, callback_err)
	}
	options.am_i_responsible = function(callback) {
		services_osvcgetrest("/compliance/modulesets/%1/am_i_responsible", [options.modset_id], "", callback)
	}
	return tags(options)
}


