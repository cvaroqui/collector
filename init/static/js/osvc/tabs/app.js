//
// app
//
function app_tabs(divid, options) {
  var o = tabs(divid)
  o.options = options

  o.load(function(){
    var i = 0

    if (!("app_id" in o.options) && ("app_name" in o.options)) {
      services_osvcgetrest("R_APPS", "", {"filters": ["app "+o.options.app_name]}, function(jd) {
        var app = jd.data[0]
        o.options.app_id = app.id
        o._load()
      })
    } else {
      o._load()
    }
  })

  o._load = function() {
    o.closetab.children("p").text(o.options.app_name ? o.options.app_name : o.options.app_id)

    // tab properties
    i = o.register_tab({
      "title": "node_tabs.properties",
      "title_class": "icon app16"
    })
    o.tabs[i].callback = function(divid) {
      app_properties(divid, o.options)
    }

    // tab quotas
    i = o.register_tab({
      "title": "array_tabs.quotas",
      "title_class": "icon quota16"
    })
    o.tabs[i].callback = function(divid) {
      table_quota_app(divid, o.options.app_name)
    }

    o.set_tab(o.options.tab)
  }
  return o
}


function app_properties(divid, options) {
	var o = {}

	// store parameters
	o.divid = divid
	o.div = $("#"+divid);
	o.options = options

	o.init = function() {
		o.info_id = o.div.find("#id");
		o.info_description = o.div.find("#description");
		o.info_app = o.div.find("#app");
		o.info_app_team_ops = o.div.find("#app_team_ops");
		o.info_app_domain = o.div.find("#app_domain");
		o.info_updated = o.div.find("#updated");
		o.info_responsibles_title = o.div.find("#responsibles_title");
		o.info_publications_title = o.div.find("#publications_title");
		o.info_responsibles = o.div.find("#responsibles");
		o.info_publications = o.div.find("#publications");
		o.info_services_title = o.div.find("#services_title");
		o.info_services = o.div.find("#services");
		o.info_nodes_title = o.div.find("#nodes_title");
		o.info_nodes = o.div.find("#nodes");

		o.load_app()
	}

	o.load_app = function() {
		services_osvcgetrest("R_APP", [o.options.app_id], "", function(jd) {
			if (!jd.data || (jd.data.length == 0)) {
				return
			}
			var data = jd.data[0]
			o.info_description.html(data.description);
			o.info_app_team_ops.html(data.app_team_ops);
			o.info_app_domain.html(data.app_domain);
			o.info_app.html(data.app);
			o.info_updated.html(osvc_date_from_collector(data.updated));
			o.info_id.html(data.id);

			var am_data = [
				{
					"title": "action_menu.data_actions",
					"class": "hd16",
					"children": [
						{
							"selector": ["tab"],
							"foldable": false,
							"cols": [],
							"children": [
								{
									"title": "action_menu.del",
									"class": "del16",
									"fn": "data_action_del_apps",
									"privileges": ["Manager", "AppManager"]
								}
							]
						}
					]
				}
			]
			tab_tools({
				"div": o.div.find("#tools"),
				"data": {"id": data.id},
				"am_data": am_data
			})

			app_publications({
				"bgcolor": "salmon",
				"tid": o.info_publications,
				"app_id": data.id
			})
			app_responsibles({
				"bgcolor": "salmon",
				"tid": o.info_responsibles,
				"app_id": data.id
			})
			tab_properties_generic_list({
				"request_service": "R_APP_SERVICES",
				"request_parameters": [data.id],
				"limit": "50",
				"key": "svcname",
				"item_class": "icon svc",
				"id": "svc_id",
				"title": "app_properties.services",
				"bgcolor": "seagreen",
				"e_title": o.info_services_title,
				"e_list": o.info_services,
				"lowercase": true,
				"ondblclick": function(divid, data) {
					service_tabs(divid, {"svc_id": data.id})
				}
			})
			tab_properties_generic_list({
				"request_service": "R_APP_NODES",
				"request_parameters": [data.id],
				"limit": "50",
				"key": "nodename",
				"item_class": "icon node16",
				"id": "node_id",
				"title": "app_properties.nodes",
				"bgcolor": "aqua",
				"e_title": o.info_nodes_title,
				"e_list": o.info_nodes,
				"lowercase": true,
				"ondblclick": function(divid, data) {
					node_tabs(divid, {"node_id": data.id})
				}
			})
			tab_properties_generic_updater({
				"div": o.div,
				"privileges": ["AppManager", "Manager"],
				"post": function(_data, callback, error_callback) {
					services_osvcpostrest("R_APP", [data.id], "", _data, callback, error_callback)
				}
			})

		})
	}

	o.div.load("/init/static/views/app_properties.html", function() {
		o.div.i18n()
		o.init()
	})

	return o

}
