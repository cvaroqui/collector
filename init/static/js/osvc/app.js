var osvc = {
 'tables': {},
 'user_groups_loaded': $.Deferred(),
 'table_settings_loaded': $.Deferred(),
 'table_filters_loaded': $.Deferred(),
 'forms_loaded': $.Deferred(),
 'i18n_started': $.Deferred(),
 'app_started': $.Deferred()
}

var _badIE=0;

function i18n_init(callback) {
  i18n.init({
      debug: true,
      getAsync : true,
      fallbackLng: false,
      load:'unspecific',
      resGetPath: "/init/static/locales/__lng__/__ns__.json",
      ns: {
          namespaces: ['translation'],
          defaultNs: 'translation'
      }
  }, function() {
     $(document).i18n()
     osvc.i18n_started.resolve(true)
  });
}

function app_start() {
  i18n_init()
  services_feed_self_and_group()
  osvc.table_settings = table_settings()
  osvc.table_filters = table_filters()
  osvc.forms = forms()

  // Check if IE and version < 10
  for (i=6; i< 10; i++) {
    if (IE(i)) _badIE=1;
    else _badIE=0;
  }

  osvc_popup_stack_listener()

  // Wait mandatory language info and User/groups info to be loaded before creating the IHM
  $.when(
      osvc.i18n_started,
      osvc.user_groups_loaded
    ).then(function() {
      osvc.menu = menu("menu_location")
      osvc.login = login("login_location")
      osvc.search = search("layout_search_tool")
      osvc.fset_selector = fset_selector("fset_selector")
      app_bindings()
      app_datetime_decorators()
      osvc.app_started.resolve(true)
    })
}

function app_load_href(href, fn, options) {
    if (!options) {
      options = {
        "disable_pushstate": false
      }
    }

    // loadable co-functions ends with '_load'
    var _href

    if (href.match(/:\/\//)) {
      // full url
      var fn_idx = 5
    } else {
      // relative url
      var fn_idx = 3
    }

    // http:, , host:port, app, ctrl, fn, arg0, arg1, ... lastarg?key=val,key=val
    var l = href.split("?")
    var v = l[0].split("/")

    v[fn_idx] += "_load"

    l[0] = v.join("/")
    _href = l.join("?")

    // update browser url and history
    if (!_badIE && !options.disable_pushstate) {
      console.log("pushstate", fn, href)
      history.pushState({"fn": fn}, "", href)
    }

    var menu = $(".header .menu16")
    menu.removeClass("menu16")
    menu.parent().prepend($("<span class='refresh16 fa-spin'></span>"))
    if ((fn != "undefined") && (fn !== "undefined") && fn) {
      console.log("load", fn)
      window[fn]("layout")
      post_load()
      return
    }
    console.log("load", _href)
    $(".layout").load(_href, {}, function (responseText, textStatus, req) {
      if (textStatus == "error") {
        // load error
        console.log("fallback to location", href)
        document.location.replace(href)
      } else {
        post_load()
      }
    })

    function post_load() {
      menu.addClass("menu16")
      menu.prev(".refresh16").remove()
      osvc.menu.set_title_from_href()
      // load success, purge tables not displayed anymore
      for (tid in osvc.tables) {
        if ($('#'+tid).length == 0) {
          delete osvc.tables[tid]
          if (tid in wsh) {
            delete wsh[tid]
          }
        }
      }
    }
}

function app_bindings() {
  // Handle navigation between load()ed pages through browser tools
  $(window).on("popstate", function(e) {
    if (e.originalEvent.state !== null) {
      if (e.state && e.state.fn) {
        fn = e.state.fn
      } else if (e.originalEvent && e.originalEvent.state && e.originalEvent.state.fn) {
        fn = e.originalEvent.state.fn
      } else {
        fn = null
      }
      console.log("popstate", location.href, fn)
      app_load_href(location.href, fn, {disable_pushstate: true});
      //e.preventDefault()
    }
  })

  // disable browser context menu expect on canvases (topology, ...)
  $(document).on('click', function(event){
    if(event.which == 2){
      event.preventDefault()
    }
  })
  $(document).on('contextmenu', function(event){
    if ($(event.target).is("canvas")) {
      return
    }
    event.preventDefault()
  })

  // key bindings
  $(document).keydown(function(event) {
    if (event.altKey) {
      return
    }

    // ESC closes pop-ups and blur inputs
    if ( event.which == 27 ) {
      $("input:focus").blur()
      $("textarea:focus").blur()
      $("#search_input").val("")
      osvc_popup_remove_from_stack();
      return
    }

    // 'TAB' from search input focuses the first visible menu_entry
    if (event.which == 9) {
      if ($('#search_input').is(":focus")) {
        $(".header").find(".menu_entry:visible").first().addClass("menu_selected")
      }
    }

    // don't honor shortcuts if a input is focused
    if ($('input').is(":focus")) {
      return
    }
    if ($('textarea').is(":focus")) {
      return
    }


    //
    // shortcuts
    //

    // 'f' for search
    if ((event.which == 70) && !event.ctrlKey) {
      if (!$('#search_input').is(":focus")) {
        event.preventDefault();
        $("[name=fset_selector]").click()
      }
    }

    // 's' for search
    else if (event.which == 83) {
      if (!$('#search_input').is(":focus")) {
        event.preventDefault();
        $('#search_input').val('');
      }
      $('#search_input').focus();
    }

    // 'n' for search
    else if (event.which == 78) {
      event.preventDefault();
      $(".header").find(".menu16").parents("ul").first().siblings(".menu").show("fold", function(){filter_menu()});
      $('#search_input').val('');
      $('#search_input').focus();
    }

    // Left
    else if (event.which == 37) {
      event.preventDefault();
      var entries = $(".header").find(".menu_entry:visible")
      var selected = entries.filter(".menu_selected")
      if ((selected.length > 0) && (entries.length > 0)) {
        entries.removeClass("menu_selected")
        var new_selected = selected.prev().addClass("menu_selected")
        if (new_selected.length == 0) {
          entries.last().addClass("menu_selected")
        }
      }
    }

    // Up
    else if (event.which == 38) {
      event.preventDefault();
      var entries = $(".header").find(".menu_entry:visible");
      var selected = entries.filter(".menu_selected")
      if ((selected.length > 0) && (entries.length > 0)) {
        var selected_index = entries.index(selected)
        var selected_y = selected.position().top
        var first_y = entries.first().position().top
        if (selected_y == first_y) {
          var candidate_entries = entries
        } else {
          var candidate_entries = entries.slice(0, selected_index)
        }
        if (selected.length == 0) {
          selected = entries.first()
        }
        if (candidate_entries.length == 0) {
          candidate_entries = entries
        }
        candidate_entries.filter(function(i, e){
          if ($(this).position().left == selected.position().left) {
            return true
          }
          return false
        }).last().each(function(){
          entries.removeClass("menu_selected");
          $(this).addClass("menu_selected");
          return;
        })
      }
    }

    // Right
    else if (event.which == 39) {
      event.preventDefault();
      var entries = $(".header").find(".menu_entry:visible")
      var selected = entries.filter(".menu_selected")
      if ((selected.length > 0) && (entries.length > 0)) {
        entries.removeClass("menu_selected")
        var new_selected = selected.next().addClass("menu_selected")
        if (new_selected.length == 0) {
          entries.first().addClass("menu_selected")
        }
      }
    }

    // Down
    else if (event.which == 40) {
      event.preventDefault();
      var entries = $(".header").find(".menu_entry:visible");
      var selected = entries.filter(".menu_selected")
      if ((selected.length > 0) && (entries.length > 0)) {
        var selected_index = entries.index(selected)
        var selected_y = selected.position().top
        var last_y = entries.last().position.top
        if (selected_y == last_y) {
          var candidate_entries = entries
        } else {
          var candidate_entries = entries.slice(selected_index+1)
        }
        if (selected.length == 0) {
          selected = entries.first()
        }
        if (candidate_entries.length == 0) {
          candidate_entries = entries
        }
        found = candidate_entries.filter(function(i, e){
          if ($(this).position().left == selected.position().left) {
            return true
          }
          return false
        }).first()
        if (found.length == 0) {
          // wrap to top
          found = entries.filter(function(i, e){
            if ($(this).position().left == selected.position().left) {
              return true
            }
            return false
          }).first()
        }
        found.each(function(){
          entries.removeClass("menu_selected")
          $(this).addClass("menu_selected")
          return
        })
      }
    }

    // 'Enter' from a menu entry does a click
    else if (is_enter(event)) {
      $(".header").find(".menu_selected:visible").each(function(){
        event.preventDefault();;
        $(this).effect("highlight");

        e = jQuery.Event("click")
        e.ctrlKey = event.ctrlKey
        $(this).trigger(e)
      })
    }


    // scroll up/down to keep selected entry displayed
    var directional_events = [37, 38, 39, 40]
    if (directional_events.indexOf(event.which) >= 0) {
      var selected = entries.filter(".menu_selected")
      var container = selected.parents(".menu,.flash").first()

      if (selected.length > 0) {
        // scroll down
        var selected_y = selected.position().top + selected.outerHeight()
        var container_y = container.position().top + container.height()
        if (container_y < selected_y) {
          container.stop().animate({
            scrollTop: container.scrollTop()+selected_y-selected.outerHeight()
          }, 500)
        }
  
        // scroll up
        var selected_y = selected.position().top
        var container_y = container.position().top
        if (container_y > selected_y) {
          container.stop().animate({
            scrollTop: container.scrollTop() + selected_y + container_y - container.height() + selected.outerHeight()
          }, 500)
        }
      }
    }
  });
}

function app_datetime_decorators() {
  var data = {
   "date_future": cell_decorator_date_future,
   "datetime_future": cell_decorator_datetime_future,
   "datetime_weekly": cell_decorator_datetime_weekly,
   "datetime_daily": cell_decorator_datetime_daily,
   "datetime_status": cell_decorator_datetime_status,
   "datetime_no_age": cell_decorator_datetime_no_age,
   "date_no_age": cell_decorator_date_no_age
  }
  osvc.interval_datetime_decorators = setInterval(function(){
    for (key in data) {
      $("."+key).each(function() {
        cell_decorators[key](this)
      })
    }
  }, 5000)
}
