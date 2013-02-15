import re
import yaml

class col_forms_yaml(HtmlTableColumn):
    def html(self, o):
        val = self.get(o)
        val = re.sub(r'(%\(\w+\)s)', r'<span class=syntax_red>\1</span>', val)
        val = re.sub(r'(\w+:)', r'<span class=syntax_green>\1</span>', val)
        return PRE(XML(val))

class table_templates(HtmlTable):
    def __init__(self, id=None, func=None, innerhtml=None):
        if id is None and 'tableid' in request.vars:
            id = request.vars.tableid
        HtmlTable.__init__(self, id, func, innerhtml)
        self.cols = ['form_name',
                     'form_type',
                     'form_folder',
                     'form_yaml',
                     'form_created',
                     'form_author']
        self.colprops = {
            'form_name': HtmlTableColumn(
                title = 'Name',
                field = 'form_name',
                display = True,
                table = 'comp_forms',
                img = 'prov'
            ),
            'form_type': col_forms_yaml(
                title = 'Type',
                field = 'form_type',
                display = True,
                table = 'comp_forms',
                img = 'edit16'
            ),
            'form_folder': HtmlTableColumn(
                title = 'Folder',
                field = 'form_folder',
                display = True,
                table = 'comp_forms',
                img = 'hd16'
            ),
            'form_yaml': col_forms_yaml(
                title = 'Definition',
                field = 'form_yaml',
                display = True,
                table = 'comp_forms',
                img = 'action16'
            ),
            'form_created': HtmlTableColumn(
                title = 'Created on',
                field = 'form_created',
                display = False,
                table = 'comp_forms',
                img = 'time16'
            ),
            'form_author': HtmlTableColumn(
                title = 'Author',
                field = 'form_author',
                display = False,
                table = 'comp_forms',
                img = 'guy16'
            ),
        }
        self.ajax_col_values = 'ajax_comp_forms_admin_col_values'
        self.dbfilterable = False
        self.checkboxes = False
        self.extrarow = True

        if 'CompFormsManager' in user_groups():
            self.additional_tools.append('add_template')

    def format_extrarow(self, o):
        d = DIV(
              A(
                _href=URL(r=request, c='comp_forms', f='comp_forms_editor', vars={'form_id': o.id}),
                _class="edit16",
              ),
            )
        return d

    def add_template(self):
        d = DIV(
              A(
                T("Add template"),
                _href=URL(r=request, f='comp_forms_editor'),
                _class='add16',
              ),
              _class='floatw',
            )
        return d

@auth.requires_membership('CompFormsManager')
def comp_forms_editor():
    q = db.comp_forms.id == request.vars.form_id
    rows = db(q).select()
    if len(rows) == 1:
        record = rows[0]
    else:
        record = None

    db.comp_forms.form_author.default = user_name()
    form = SQLFORM(db.comp_forms,
                 record=record,
                 deletable=True,
                 fields=['form_name',
                         'form_folder',
                         'form_type',
                         'form_yaml',],
                 labels={'form_name': T('Form name'),
                         'form_folder': T('Form folder'),
                         'form_type': T('Form type'),
                         'form_yaml': T('Form yaml definition')}
                )
    if form.accepts(request.vars):
        if request.vars.form_id is None:
            _log('compliance.form.add',
                 "Created '%(form_type)s' form '%(form_name)s' with definition:\n%(form_yaml)s",
                     dict(form_name=request.vars.form_name,
                          form_type=request.vars.form_type,
                          form_yaml=request.vars.form_yaml))
        elif request.vars.delete_this_record == 'on':
            _log('compliance.form.delete',
                 "Deleted '%(form_type)s' form '%(form_name)s' with definition:\n%(form_yaml)s",
                     dict(form_name=request.vars.form_name,
                          form_type=request.vars.form_type,
                          form_yaml=request.vars.form_yaml))
        else:
            _log('compliance.form.change',
                 "Changed '%(form_type)s' form '%(form_name)s' with definition:\n%(form_yaml)s",
                     dict(form_name=request.vars.form_name,
                          form_type=request.vars.form_type,
                          form_yaml=request.vars.form_yaml))

        session.flash = T("template recorded")
        redirect(URL(r=request, c='comp_forms', f='comp_forms_admin'))
    elif form.errors:
        response.flash = T("errors in form")
    return dict(form=form)

@auth.requires_login()
def ajax_comp_forms_admin():
    t = table_templates('templates', 'ajax_comp_forms_admin')

    o = db.comp_forms.form_name
    q = db.comp_forms.id > 0
    for f in t.cols:
        q = _where(q, t.colprops[f].table, t.filter_parse(f), f)
    n = db(q).count()
    t.setup_pager(n)
    t.object_list = db(q).select(limitby=(t.pager_start,t.pager_end), orderby=o)
    return t.html()

@auth.requires_login()
def comp_forms_admin():
    t = DIV(
          ajax_comp_forms_admin(),
          _id='templates',
        )
    return dict(table=t)

def get_folders_info():
    h = {}
    for id, form_name, form_folder, data in get_forms("folder"):
        if 'Folder' not in data:
            continue
        if 'FolderCss' not in data:
            data['FolderCss'] = 'folder48'
        if 'FolderDesc' not in data:
            data['FolderCss'] = ''
        h[data['Folder']] = data
    return data

def get_forms(form_type=None, folder="/"):
    q = db.comp_forms.form_folder == folder

    if form_type is None:
        pass
    elif type(form_type) == list:
        q &= db.comp_forms.form_type.belongs(form_type)
    else:
        q &= db.comp_forms.form_type == form_type

    rows = db(q).select(orderby=db.comp_forms.form_type|db.comp_forms.form_name)
    l = []
    for row in rows:
        try:
            data = yaml.load(row.form_yaml)
        except:
            data = {}
        l.append((row.id, row.form_name, row.form_folder, data))
    return l

@auth.requires_login()
def ajax_comp_forms_list():
    return comp_forms_list(request.vars.folder)

@auth.requires_login()
def comp_forms_list(folder="/"):
    import os
    l = []

    folder = os.path.realpath(folder)
    folders = get_forms("folder", folder=folder)

    if folder != "/":
        parent_folder = '/'.join(folder.split('/')[:-1])
        if not parent_folder.startswith('/'):
            parent_folder = '/'+parent_folder
        parent_data = {
          'FolderName': '',
          'FolderCss': 'parent48',
          'FolderLabel': 'Parent folder',
          'FolderDesc': parent_folder,
        }
        parent = ('parent', 'parent', parent_folder, parent_data)
        folders = [parent] + folders

    for id, form_name, form_folder, data in folders:
        cl = data.get('FolderCss', 'folder48')
        desc = data.get('FolderDesc', '')
        folderlabel = data.get('FolderLabel', form_name)
        l.append(DIV(
          DIV(
            P(folderlabel),
            P(desc, _style="font-style:italic;padding-left:1em"),
            _style="padding-top:1em;padding-bottom:1em;",
            _class=cl,
          ),
          _onclick="""
sync_ajax('%(url)s', [], '%(id)s', function(){eval_js_in_ajax_response('%(id)s')});
"""%dict(
                id="comp_forms_list",
                url=URL(
                  r=request, c='comp_forms', f='ajax_comp_forms_list',
                  vars={
                    "folder": os.path.join(form_folder, data.get('FolderName')),
                  }
                ),
),
          _class="formentry",
        ),
      )

    for id, form_name, form_folder, data in get_forms("custo", folder=folder):
        cl = data.get('Css', 'nologo48')
        desc = data.get('Desc', '')
        l.append(DIV(
          DIV(
            P(form_name),
            P(desc, _style="font-style:italic;padding-left:1em"),
            _style="padding-top:1em;padding-bottom:1em;",
            _class=cl,
          ),
          _onclick="""
$(this).closest("table").children().children().each(function(){
  $(this).toggle()
})
$(this).closest("tr").each(function(){
  $(this).toggle()
})
$("#comp_forms_inputs").each(function(){
  $(this).text('');
  $(this).slideToggle(400);
})
$('[name=radio_form]').each(function(){
  if ($(this).attr("id")=='%(rid)s'){return};
  $(this).prop('checked', false)
});
sync_ajax('%(url)s', [], '%(id)s', function(){eval_js_in_ajax_response('%(id)s')});
"""%dict(
                id="comp_forms_inputs",
                rid=id,
                url=URL(
                  r=request, c='compliance', f='ajax_comp_forms_inputs',
                  vars={
                    "form_id": id,
                    "hid": "comp_forms_inputs",
                  }
                ),
              ),
          _class="formentry",
        ),
      )
    d = DIV(
          H1(T("Choose a customization form")),
          DIV(l),
          DIV(
            _id="comp_forms_inputs",
            _style="padding-top:3em;display:none",
          ),
          _style="padding:2em;max-width:40em;",
        )
    return d

@auth.requires_login()
def comp_forms():
    d = DIV(
      ajax_target(),
      DIV(comp_forms_list(), _id="comp_forms_list"),
    )
    return dict(table=d)

@auth.requires_login()
def ajax_target():
    l = []
    l.append(TR(
          TD(
            H1(T("Choose target to customize")),
            _colspan=4,
          ),
        ))
    l.append(TR(
          TD(
            INPUT(
              _value=False,
              _type='radio',
              _id="radio_service",
              _onclick="""
$("#radio_node").prop('checked',false);
$("#stage2").html("");
$("#stage3").html("");
$("#stage4").html("");
sync_ajax('%(url)s', [], '%(id)s', function(){eval_js_in_ajax_response('%(id)s')})"""%dict(
                id="stage1",
                url=URL(r=request, c='comp_forms', f='ajax_service_list'),
              ),
            ),
          ),
          TD(
            T("Customize service"),
          ),
          TD(
            INPUT(
              _value=False,
              _type='radio',
              _id="radio_node",
              _onclick="""
$("#radio_service").prop('checked',false);
$("#stage2").html("");
$("#stage3").html("");
$("#stage4").html("");
sync_ajax('%(url)s', [], '%(id)s', function(){eval_js_in_ajax_response('%(id)s')})"""%dict(
                id="stage1",
                url=URL(r=request, c='comp_forms', f='ajax_node_list'),
              ),
            ),
          ),
          TD(
            T("Customize node"),
          ),
        ))
    d = DIV(
          TABLE(l),
          DIV(
            _id="stage1",
          ),
          DIV(
            _id="stage2",
            _style="padding:2em",
          ),
        )
    return d

@auth.requires_login()
def ajax_node_list():
    o = db.nodes.project | db.nodes.nodename
    q = db.nodes.id > 0
    if 'Manager' not in user_groups():
        q &= db.apps_responsibles.app_id == db.apps.id
        q &= db.apps_responsibles.group_id == db.auth_membership.group_id
        q &= db.auth_membership.user_id == auth.user_id
        q &= db.auth_membership.group_id == db.auth_group.id
        q &= db.nodes.team_responsible == db.auth_group.role
    nodes = db(q).select(db.nodes.nodename,
                         db.nodes.project,
                         groupby=o,
                         orderby=o)

    l = [OPTION(T("Choose one"))]
    for n in nodes:
        o = OPTION(
                "%s - %s"%(str(n.project).upper(), str(n.nodename).lower()),
                _value=n.nodename
            )
        l.append(o)

    return DIV(
             H3(T("Node")),
             SELECT(
               l,
               _id="nodename",
               _onchange="""
$("#stage2").html('%(spinner)s');
ajax('%(url)s/%(objtype)s/'+this.options[this.selectedIndex].value, [], '%(div)s');
"""%dict(
      url=URL(
            r=request, c='compliance',
            f='ajax_custo',
          ),
      objtype='nodename',
      div="stage2",
      spinner=IMG(_src=URL(r=request,c='static',f='spinner.gif')).xml(),
    ),
             ),
             SCRIPT("""
$("select").combobox();
$("#nodename").siblings("input").focus();
""", _name="stage1_to_eval"),
           )

@auth.requires_login()
def ajax_service_list():
    o = db.services.svc_app | db.services.svc_name
    q = db.services.svc_app == db.apps.app
    q &= db.services.svc_name == db.svcmon.mon_svcname
    if 'Manager' not in user_groups():
        q &= db.apps_responsibles.app_id == db.apps.id
        q &= db.apps_responsibles.group_id == db.auth_membership.group_id
        q &= db.auth_membership.user_id == auth.user_id
    services = db(q).select(db.services.svc_name,
                            db.services.svc_app,
                            groupby=o,
                            orderby=o)

    l = [OPTION(T("Choose one"))]
    for s in services:
        o = OPTION(
                "%s - %s"%(str(s.svc_app).upper(), str(s.svc_name).lower()),
                _value=s.svc_name
            )
        l.append(o)

    return DIV(
             H3(T("Service")),
             SELECT(
               l,
               _id="svcname",
               _onchange="""
$("#stage2").html('%(spinner)s');
ajax('%(url)s/%(objtype)s/'+this.options[this.selectedIndex].value, [], '%(div)s');
"""%dict(
      url=URL(
            r=request, c='compliance',
            f='ajax_custo',
          ),
      objtype='svcname',
      div="stage2",
      spinner=IMG(_src=URL(r=request,c='static',f='spinner.gif')).xml(),
    ),

             ),
             SCRIPT("""
$("select").combobox();
$("#svcname").siblings("input").focus();
""", _name="stage1_to_eval"),
           )

