# coding: utf8

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import datetime

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()

#
# XMLRPC
#
#########
def auth_uuid(fn):
    def new(*args):
        uuid, node = args['auth']
        rows = db(db.auth_node.nodename==node&db.auth_node.uuid==uuid).select()
        if len(rows) != 1:
            return
        return fn(*args)
    return new

@auth_uuid
@service.xmlrpc
def delete_services(hostid=None, auth=("", "")):
    if hostid is None:
        return 0
    db(db.services.svc_hostid==hostid).delete()
    db.commit()
    return 0

@auth_uuid
@service.xmlrpc
def delete_service_list(hostid=None, svcnames=[], auth=("", "")):
    if hostid is None or len(svcnames) == 0:
        return 0
    for svcname in svcnames:
        q = (db.services.svc_name==svcname)
        q &= (db.services.svc_hostid==hostid)
        db(q).delete()
        db.commit()
    return 0

@auth_uuid
@service.xmlrpc
def begin_action(vars, vals, auth):
    sql="""insert into SVCactions (%s) values (%s)""" % (','.join(vars), ','.join(vals))
    db.executesql(sql)
    db.commit()
    h = {}
    for a, b in zip(vars, vals):
        h[a] = b
    if 'cron' not in h or h['cron'] == '0':
        _log("service.action",
             "action '%(a)s' on %(svc)s@%(node)s",
             dict(a=h['action'].strip("'"),
                  svc=h['svcname'].strip("'"),
                  node=h['hostname'].strip("'")),
             svcname=h['svcname'].strip("'"),
             nodename=h['hostname'].strip("'"))
    return 0

@auth_uuid
@service.xmlrpc
def res_action(vars, vals, auth):
    upd = []
    for a, b in zip(vars, vals):
        upd.append("%s=%s" % (a, b))
    sql="""insert delayed into SVCactions (%s) values (%s)""" % (','.join(vars), ','.join(vals))
    db.executesql(sql)
    db.commit()
    return 0

@auth_uuid
@service.xmlrpc
def end_action(vars, vals, auth):
    upd = []
    h = {}
    for a, b in zip(vars, vals):
        h[a] = b
        if a not in ['hostname', 'svcname', 'begin', 'action', 'hostid']:
            upd.append("%s=%s" % (a, b))
    sql="""update SVCactions set %s where hostname=%s and svcname=%s and begin=%s and action=%s""" %\
        (','.join(upd), h['hostname'], h['svcname'], h['begin'], h['action'])
    #raise Exception(sql)
    db.executesql(sql)
    db.commit()
    if h['action'].strip("'") in ('start', 'startcontainer') and \
       h['status'].strip("'") == 'ok':
        update_virtual_asset(h['hostname'].strip("'"), h['svcname'].strip("'"))
    if h['status'].strip("'") == 'err':
        update_action_errors(h['svcname'], h['hostname'])
        h['svcname'] = h['svcname'].strip('\\').strip("'")
        _log("service.action",
             "action '%(a)s' error on %(svc)s@%(node)s",
             dict(a=h['action'].strip("'"),
                  svc=h['svcname'].strip("'"),
                  node=h['hostname'].strip("'")),
             svcname=h['svcname'].strip("'"),
             nodename=h['hostname'].strip("'"),
             level="error")
    return 0

def update_action_errors(svcname, nodename):
    sql = """insert into b_action_errors set svcname=%(svcname)s, nodename=%(nodename)s, err=(
               select count(a.id) from SVCactions a
                 where a.svcname = %(svcname)s and
                       a.hostname = %(nodename)s and
                       a.status = 'err' and
                       ((a.ack <> 1) or isnull(a.ack)))
             on duplicate key update err=(
               select count(a.id) from SVCactions a
                 where a.svcname = %(svcname)s and
                       a.hostname = %(nodename)s and
                       a.status = 'err' and
                       ((a.ack <> 1) or isnull(a.ack)))
          """%dict(svcname=svcname, nodename=nodename)
    #raise Exception(sql)
    db.executesql(sql)

def update_virtual_asset(nodename, svcname):
    q = db.services.svc_name == svcname
    svc = db(q).select(db.services.svc_vmname).first()
    if svc is None:
        return
    q = db.nodes.nodename == nodename
    node = db(q).select().first()
    if node is None:
        return
    fields = ['loc_addr', 'loc_city', 'loc_zip', 'loc_room', 'loc_building',
              'loc_floor', 'loc_rack', 'power_cabinet1', 'power_cabinet2',
              'power_supply_nb', 'power_protect', 'power_protect_breaker',
              'power_breaker1', 'power_breaker2', 'loc_country']
    sql = "update nodes set "
    for f in fields:
        sql += "%s='%s',"%(f, node[f])
    sql = sql.rstrip(',')
    sql += "where nodename='%s'"%svc.svc_vmname
    db.executesql(sql)

@auth_uuid
@service.xmlrpc
def update_appinfo(vars, vals, auth):
    h = {}
    for a,b in zip(vars, vals[0]):
        h[a] = b
    db.executesql("delete from appinfo where app_svcname='%s'"%h['app_svcname'])
    generic_insert('appinfo', vars, vals)

@auth_uuid
@service.xmlrpc
def update_service(vars, vals, auth):
    if 'svc_hostid' not in vars:
        return
    if 'updated' not in vars:
        vars += ['updated']
        vals += [datetime.datetime.now()]
    generic_insert('services', vars, vals)

@auth_uuid
@service.xmlrpc
def push_checks(vars, vals, auth):
    """
        chk_nodename
        chk_svcname
        chk_type
        chk_instance
        chk_value
        chk_updated
    """
    generic_insert('checks_live', vars, vals)
    q = db.checks_live.id < 0
    for v in vals:
        qr = db.checks_live.chk_nodename == v[0]
        qr &= db.checks_live.chk_type == v[2]
        qr &= db.checks_live.chk_instance == v[3]
        q |= qr
    rows = db(q).select()
    update_thresholds_batch(rows)

@auth_uuid
@service.xmlrpc
def update_asset(vars, vals, auth):
    now = datetime.datetime.now()
    vars.append('updated')
    vals.append(now)
    generic_insert('nodes', vars, vals)

@auth_uuid
@service.xmlrpc
def res_action_batch(vars, vals, auth):
    generic_insert('SVCactions', vars, vals)

def _resmon_clean(node, svcname):
    if node is None or node == '':
        return 0
    if svcname is None or svcname == '':
        return 0
    q = db.resmon.nodename==node.strip("'")
    q &= db.resmon.svcname==svcname.strip("'")
    db(q).delete()
    db.commit()

@auth_uuid
@service.xmlrpc
def resmon_update(vars, vals, auth):
    _resmon_update(vars, vals)

def _resmon_update(vars, vals):
    if len(vals) == 0:
        return
    if isinstance(vals[0], list):
        for v in vals:
            __resmon_update(vars, v)
    else:
        __resmon_update(vars, vals)

def __resmon_update(vars, vals):
    h = {}
    for a,b in zip(vars, vals[0]):
        h[a] = b
    if 'nodename' in h and 'svcname' in h:
        _resmon_clean(h['nodename'], h['svcname'])
    generic_insert('resmon', vars, vals)

@auth_uuid
@service.xmlrpc
def svcmon_update_combo(g_vars, g_vals, r_vars, r_vals, auth):
    _svcmon_update(g_vars, g_vals)
    _resmon_update(r_vars, r_vals)

@auth_uuid
@service.xmlrpc
def register_disk(vars, vals, auth):
    generic_insert('svcdisks', vars, vals)

@auth_uuid
@service.xmlrpc
def register_sync(vars, vals, auth):
    pass

@auth_uuid
@service.xmlrpc
def register_ip(vars, vals, auth):
    pass

@auth_uuid
@service.xmlrpc
def register_fs(vars, vals, auth):
    pass

@auth_uuid
@service.xmlrpc
def insert_stats_fs_u(vars, vals, auth):
    generic_insert('stats_fs_u', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_cpu(vars, vals, auth):
    generic_insert('stats_cpu', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_mem_u(vars, vals, auth):
    generic_insert('stats_mem_u', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_proc(vars, vals, auth):
    generic_insert('stats_proc', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_swap(vars, vals, auth):
    generic_insert('stats_swap', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_block(vars, vals, auth):
    generic_insert('stats_block', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_blockdev(vars, vals, auth):
    generic_insert('stats_blockdev', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_netdev(vars, vals, auth):
    generic_insert('stats_netdev', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats_netdev_err(vars, vals, auth):
    generic_insert('stats_netdev_err', vars, vals)

@auth_uuid
@service.xmlrpc
def insert_stats(data, auth):
    import cPickle
    h = cPickle.loads(data)
    for stat in h:
        vars, vals = h[stat]
        generic_insert('stats_'+stat, vars, vals)

@auth_uuid
@service.xmlrpc
def insert_pkg(vars, vals, auth):
    generic_insert('packages', vars, vals)

@auth_uuid
@service.xmlrpc
def update_sym_xml(symid, vars, vals, auth):
    import os

    dir = 'applications'+str(URL(r=request,c='uploads',f='symmetrix'))
    if not os.path.exists(dir):
        os.makedirs(dir)

    dir = os.path.join(dir, symid)
    if not os.path.exists(dir):
        os.makedirs(dir)

    for a,b in zip(vars, vals):
        a = os.path.join(dir, a)
        try:
            f = open(a, 'w')
            f.write(b)
            f.close()
        except:
            pass

    symmetrix = local_import('symmetrix', reload=True)
    s = symmetrix.get_sym(dir)
    if s is None:
        return

    #
    # better to create hashes from the batch rather than
    # during an interactive session
    #
    s.get_sym_all()

    #
    # populate the diskinfo table
    #
    vars = ['disk_id', 'disk_devid', 'disk_arrayid']
    vals = []
    for devname, dev in s.dev.items():
        vals.append([dev.wwn, devname, symid])
    generic_insert('diskinfo', vars, vals)

@auth_uuid
@service.xmlrpc
def delete_pkg(node, auth):
    if node is None or node == '':
        return 0
    db(db.packages.pkg_nodename==node).delete()
    db.commit()

@auth_uuid
@service.xmlrpc
def insert_patch(vars, vals, auth):
    generic_insert('patches', vars, vals)

@auth_uuid
@service.xmlrpc
def delete_patch(node, auth):
    if node is None or node == '':
        return 0
    db(db.patches.patch_nodename==node).delete()
    db.commit()

@auth_uuid
@service.xmlrpc
def delete_syncs(svcname, auth):
    pass

@auth_uuid
@service.xmlrpc
def delete_ips(svcname, node, auth):
    pass

@auth_uuid
@service.xmlrpc
def delete_fss(svcname, auth):
    pass

@auth_uuid
@service.xmlrpc
def delete_disks(svcname, node, auth):
    if svcname is None or svcname == '':
        return 0
    db((db.svcdisks.disk_svcname==svcname)&(db.svcdisks.disk_nodename==node)).delete()
    db.commit()

@service.xmlrpc
def register_node(node):
    if node is None or node == '':
        return ["no node name provided"]
    q = db.auth_node.nodename == node
    rows = db(q).select()
    if len(rows) != 0:
        _log("node.register",
             "node '%(node)s' double registration attempt",
             dict(node=node),
             nodename=node,
             level="warning")
        return ["already registered"]
    import uuid
    u = str(uuid.uuid4())
    db.auth_node.insert(nodename=node, uuid=u)
    db.commit()
    _log("node.register",
         "node '%(node)s' registered",
         dict(node=node),
         nodename=node)
    return u

@auth_uuid
@service.xmlrpc
def svcmon_update(vars, vals, auth):
    _svcmon_update(vars, vals)

def _svcmon_update(vars, vals):
    if len(vals) == 0:
        return
    if isinstance(vals[0], list):
        for v in vals:
            __svcmon_update(vars, v)
    else:
        __svcmon_update(vars, vals)

def compute_availstatus(h):
    def status_merge_down(s):
        if s == 'up': return 'warn'
        elif s == 'down': return 'down'
        elif s == 'stdby down': return 'stdby down'
        elif s == 'stdby up': return 'stdby up with down'
        elif s == 'stdby up with up': return 'warn'
        elif s == 'stdby up with down': return 'stdby up with down'
        elif s in ['undef', 'n/a']: return 'down'
        else: return 'undef'

    def status_merge_up(s):
        if s == 'up': return 'up'
        elif s == 'down': return 'warn'
        elif s == 'stdby down': return 'warn'
        elif s == 'stdby up': return 'stdby up with up'
        elif s == 'stdby up with up': return 'stdby up with up'
        elif s == 'stdby up with down': return 'warn'
        elif s in ['undef', 'n/a']: return 'up'
        else: return 'undef'

    def status_merge_stdby_up(s):
        if s == 'up': return 'stdby up with up'
        elif s == 'down': return 'stdby up with down'
        elif s == 'stdby down': return 'warn'
        elif s == 'stdby up': return 'stdby up'
        elif s == 'stdby up with up': return 'stdby up with up'
        elif s == 'stdby up with down': return 'stdby up with down'
        elif s in ['undef', 'n/a']: return 'stdby up'
        else: return 'undef'

    def status_merge_stdby_down(s):
        if s == 'up': return 'stdby down with up'
        elif s == 'down': return 'stdby down'
        elif s == 'stdby down': return 'stdby down'
        elif s == 'stdby up': return 'warn'
        elif s == 'stdby up with up': return 'warn'
        elif s == 'stdby up with down': return 'warn'
        elif s in ['undef', 'n/a']: return 'stdby down'
        else: return 'undef'

    s = 'undef'
    for sn in ['mon_containerstatus',
              'mon_ipstatus',
              'mon_fsstatus',
              'mon_appstatus',
              'mon_diskstatus']:
        if h[sn] in ['warn', 'todo']: return 'warn'
        elif h[sn] == 'undef': return 'undef'
        elif h[sn] == 'n/a':
            if s == 'undef': s = 'n/a'
            else: continue
        elif h[sn] == 'up': s = status_merge_up(s)
        elif h[sn] == 'down': s = status_merge_down(s)
        elif h[sn] == 'stdby up': s = status_merge_stdby_up(s)
        elif h[sn] == 'stdby down': s = status_merge_stdby_down(s)
        else: return 'undef'
    if s == 'stdby up with up':
        s = 'up'
    elif s == 'stdby up with down':
        s = 'stdby up'
    return s

def svc_status_update(svcname):
    """ avail and overall status can be:
        up, down, stdby up, stdby down, warn, undef
    """
    q = db.svcmon.mon_svcname == svcname
    rows = db(q).select(db.svcmon.mon_overallstatus,
                        db.svcmon.mon_availstatus,
                        db.svcmon.mon_updated)

    tlim = datetime.datetime.now() - datetime.timedelta(minutes=15)
    ostatus_l = [r.mon_overallstatus for r in rows if r.mon_updated > tlim]
    astatus_l = [r.mon_availstatus for r in rows if r.mon_updated > tlim]
    n_trusted_nodes = len(ostatus_l)
    n_nodes = len(rows)
    ostatus_l = set(ostatus_l)
    astatus_l = set(astatus_l)

    ostatus = 'undef'
    astatus = 'undef'

    if 'up' in astatus_l:
        astatus = 'up'
    elif n_trusted_nodes == 0:
        astatus = 'undef'
    else:
        if astatus_l == set(['n/a']):
            astatus = 'n/a'
        elif 'warn' in astatus_l:
            astatus = 'warn'
        else:
            astatus = 'down'

    if n_trusted_nodes < n_nodes:
        ostatus = 'warn'
    elif n_trusted_nodes == 0:
        ostatus = 'undef'
    elif 'warn' in ostatus_l or \
         'stdby down' in ostatus_l or \
         'undef' in ostatus_l:
        ostatus = 'warn'
    elif set(['up']) == ostatus_l or \
         set(['up', 'down']) == ostatus_l or \
         set(['up', 'stdby up']) == ostatus_l or \
         set(['up', 'down', 'stdby up']) == ostatus_l or \
         set(['up', 'down', 'stdby up', 'n/a']) == ostatus_l:
        ostatus = 'up'
    elif set(['down']) == ostatus_l or \
         set(['down', 'stdby up']) == ostatus_l or \
         set(['down', 'stdby up', 'n/a']) == ostatus_l:
        ostatus = 'down'
    else:
        ostatus = 'undef'

    svc_log_update(svcname, astatus)

    db(db.services.svc_name==svcname).update(
      svc_status=ostatus,
      svc_availstatus=astatus)

def svc_log_update(svcname, astatus):
    q = db.services_log.svc_name == svcname
    o = ~db.services_log.id
    rows = db(q).select(orderby=o, limitby=(0,1))
    end = datetime.datetime.now()
    if len(rows) == 1:
        prev = rows[0]
        if prev.svc_availstatus == astatus:
            id = prev.id
            q = db.services_log.id == id
            db(q).update(svc_end=end)
        else:
            db.services_log.insert(svc_name=svcname,
                                   svc_begin=prev.svc_end,
                                   svc_end=end,
                                   svc_availstatus=astatus)
    else:
        db.services_log.insert(svc_name=svcname,
                               svc_begin=end,
                               svc_end=end,
                               svc_availstatus=astatus)

def __svcmon_update(vars, vals):
    # don't trust the server's time
    h = {}
    for a,b in zip(vars, vals):
        if a == 'mon_updated':
            continue
        h[a] = b
    now = datetime.datetime.now()
    tmo = now - datetime.timedelta(minutes=15)
    h['mon_updated'] = now
    if 'mon_hbstatus' not in h:
        h['mon_hbstatus'] = 'undef'
    if 'mon_availstatus' not in h:
        h['mon_availstatus'] = compute_availstatus(h)
    generic_insert('svcmon', h.keys(), h.values())
    svc_status_update(h['mon_svcname'])

    query = db.svcmon_log.mon_svcname==h['mon_svcname']
    query &= db.svcmon_log.mon_nodname==h['mon_nodname']
    last = db(query).select(orderby=~db.svcmon_log.id, limitby=(0,1))
    if len(last) == 0:
        _vars = ['mon_begin',
                 'mon_end',
                 'mon_svcname',
                 'mon_nodname',
                 'mon_overallstatus',
                 'mon_availstatus',
                 'mon_ipstatus',
                 'mon_fsstatus',
                 'mon_diskstatus',
                 'mon_containerstatus',
                 'mon_appstatus',
                 'mon_syncstatus',
                 'mon_hbstatus']
        _vals = [h['mon_updated'],
                 h['mon_updated'],
                 h['mon_svcname'],
                 h['mon_nodname'],
                 h['mon_overallstatus'],
                 h['mon_availstatus'],
                 h['mon_ipstatus'],
                 h['mon_fsstatus'],
                 h['mon_diskstatus'],
                 h['mon_containerstatus'],
                 h['mon_appstatus'],
                 h['mon_syncstatus'],
                 h['mon_hbstatus']]
        generic_insert('svcmon_log', _vars, _vals)
        if h['mon_overallstatus'] == 'warn':
            level = "warning"
        else:
            level = "info"
        _log("service.status",
             "service '%(svc)s' state initialized on '%(node)s': avail(%(a1)s=>%(a2)s) overall(%(o1)s=>%(o2)s)",
             dict(
               svc=h['mon_svcname'],
               node=h['mon_nodname'],
               a1="none",
               a2=h['mon_availstatus'],
               o1="none",
               o2=h['mon_overallstatus']),
             svcname=h['mon_svcname'],
             nodename=h['mon_nodname'],
             level=level)
    elif last[0].mon_end < tmo:
        _vars = ['mon_begin',
                 'mon_end',
                 'mon_svcname',
                 'mon_nodname',
                 'mon_overallstatus',
                 'mon_availstatus',
                 'mon_ipstatus',
                 'mon_fsstatus',
                 'mon_diskstatus',
                 'mon_containerstatus',
                 'mon_appstatus',
                 'mon_syncstatus',
                 'mon_hbstatus']
        _vals = [last[0].mon_end,
                 h['mon_updated'],
                 h['mon_svcname'],
                 h['mon_nodname'],
                 "undef",
                 "undef",
                 "undef",
                 "undef",
                 "undef",
                 "undef",
                 "undef",
                 "undef",
                 "undef"]
        generic_insert('svcmon_log', _vars, _vals)
        _vars = ['mon_begin',
                 'mon_end',
                 'mon_svcname',
                 'mon_nodname',
                 'mon_overallstatus',
                 'mon_availstatus',
                 'mon_ipstatus',
                 'mon_fsstatus',
                 'mon_diskstatus',
                 'mon_containerstatus',
                 'mon_appstatus',
                 'mon_syncstatus',
                 'mon_hbstatus']
        _vals = [h['mon_updated'],
                 h['mon_updated'],
                 h['mon_svcname'],
                 h['mon_nodname'],
                 h['mon_overallstatus'],
                 h['mon_availstatus'],
                 h['mon_ipstatus'],
                 h['mon_fsstatus'],
                 h['mon_diskstatus'],
                 h['mon_containerstatus'],
                 h['mon_appstatus'],
                 h['mon_hbstatus'],
                 h['mon_syncstatus']]
        generic_insert('svcmon_log', _vars, _vals)
        if h['mon_overallstatus'] == 'warn':
            level = "warning"
        else:
            level = "info"
        _log("service.status",
             "service '%(svc)s' state changed on '%(node)s': avail(%(a1)s=>%(a2)s) overall(%(o1)s=>%(o2)s)",
             dict(
               svc=h['mon_svcname'],
               node=h['mon_nodname'],
               a1="undef",
               a2=h['mon_availstatus'],
               o1="undef",
               o2=h['mon_overallstatus']),
             svcname=h['mon_svcname'],
             nodename=h['mon_nodname'],
             level=level)
    elif h['mon_overallstatus'] != last[0].mon_overallstatus or \
         h['mon_availstatus'] != last[0].mon_availstatus:
        _vars = ['mon_begin',
                 'mon_end',
                 'mon_svcname',
                 'mon_nodname',
                 'mon_overallstatus',
                 'mon_availstatus',
                 'mon_ipstatus',
                 'mon_fsstatus',
                 'mon_diskstatus',
                 'mon_containerstatus',
                 'mon_appstatus',
                 'mon_syncstatus',
                 'mon_hbstatus']
        _vals = [h['mon_updated'],
                 h['mon_updated'],
                 h['mon_svcname'],
                 h['mon_nodname'],
                 h['mon_overallstatus'],
                 h['mon_availstatus'],
                 h['mon_ipstatus'],
                 h['mon_fsstatus'],
                 h['mon_diskstatus'],
                 h['mon_containerstatus'],
                 h['mon_appstatus'],
                 h['mon_syncstatus'],
                 h['mon_hbstatus']]
        generic_insert('svcmon_log', _vars, _vals)
        db(db.svcmon_log.id==last[0].id).update(mon_end=h['mon_updated'])
        if h['mon_overallstatus'] == 'warn':
            level = "warning"
        else:
            level = "info"
        _log("service.status",
             "service '%(svc)s' state changed on '%(node)s': avail(%(a1)s=>%(a2)s) overall(%(o1)s=>%(o2)s)",
             dict(
               svc=h['mon_svcname'],
               node=h['mon_nodname'],
               a1=last[0].mon_availstatus,
               a2=h['mon_availstatus'],
               o1=last[0].mon_overallstatus,
               o2=h['mon_overallstatus']),
             svcname=h['mon_svcname'],
             nodename=h['mon_nodname'],
             level=level)
    else:
        db(db.svcmon_log.id==last[0].id).update(mon_end=h['mon_updated'])

def get_defaults(row):
    q = db.checks_defaults.chk_type == row.chk_type
    rows = db(q).select()
    if len(rows) == 0:
        return
    return (rows[0].chk_low, rows[0].chk_high, 'defaults')

def get_settings(row):
    q = db.checks_settings.chk_nodename == row.chk_nodename
    q &= db.checks_settings.chk_type == row.chk_type
    q &= db.checks_settings.chk_instance == row.chk_instance
    rows = db(q).select()
    if len(rows) == 0:
        return
    return (rows[0].chk_low, rows[0].chk_high, 'settings')

def get_filters(row):
    qr = db.gen_filterset_check_threshold.chk_type == row.chk_type
    q1 = db.gen_filterset_check_threshold.chk_instance == row.chk_instance
    q2 = db.gen_filterset_check_threshold.chk_instance == None
    q3 = db.gen_filterset_check_threshold.chk_instance == ""
    qr &= (q1|q2|q3)
    fsets = db(qr).select()
    if len(fsets) == 0:
        return
    for fset in fsets:
        qr = db.v_gen_filtersets.fset_id == fset.fset_id
        filters = db(qr).select(db.v_gen_filtersets.ALL, orderby=db.v_gen_filtersets.f_order|db.v_gen_filtersets.id)
        if len(filters) == 0:
            continue
        qr = db.nodes.nodename == row.chk_nodename
        qr &= db.nodes.nodename == db.svcmon.mon_nodname
        qr &= db.svcmon.mon_svcname == db.services.svc_name
        for f in filters:
            qr = comp_query(qr, f)
        n = db(qr).count()
        if n == 0:
            continue
        return (fset.chk_low, fset.chk_high, 'fset: '+f.fset_name)
    return

def update_thresholds_batch(rows=None):
    # maintenance batch
    if rows is None:
        q = db.checks_live.id > 0
        rows = db(q).select()
    for row in rows:
        update_thresholds(row)

def update_thresholds(row):
    # try to find most precise settings
    t = get_settings(row)
    if t is not None:
        db(db.checks_live.id==row.id).update(chk_low=t[0], chk_high=t[1], chk_threshold_provider=t[2])
        return

    # try to find filter-match thresholds
    t = get_filters(row)
    if t is not None:
        db(db.checks_live.id==row.id).update(chk_low=t[0], chk_high=t[1], chk_threshold_provider=t[2])
        return

    # try to find least precise settings (ie defaults)
    t = get_defaults(row)
    if t is not None:
        db(db.checks_live.id==row.id).update(chk_low=t[0], chk_high=t[1], chk_threshold_provider=t[2])
        return

    # no threshold found, leave as-is
    return

def comp_query(q, row):
    if 'v_gen_filtersets' in row:
        v = row.v_gen_filtersets
    else:
        v = row
    if v.encap_fset_id > 0:
        o = db.v_gen_filtersets.f_order
        qr = db.v_gen_filtersets.fset_id == v.encap_fset_id
        rows = db(qr).select(orderby=o)
        qry = None
        for r in rows:
            qry = comp_query(qry, r)
    else:
        if v.f_op == '=':
            qry = db[v.f_table][v.f_field] == v.f_value
        elif v.f_op == '!=':
            qry = db[v.f_table][v.f_field] != v.f_value
        elif v.f_op == 'LIKE':
            qry = db[v.f_table][v.f_field].like(v.f_value)
        elif v.f_op == 'NOT LIKE':
            qry = ~db[v.f_table][v.f_field].like(v.f_value)
        elif v.f_op == 'IN':
            qry = db[v.f_table][v.f_field].belongs(v.f_value.split(','))
        elif v.f_op == 'NOT IN':
            qry = ~db[v.f_table][v.f_field].belongs(v.f_value.split(','))
        elif v.f_op == '>=':
            qry = db[v.f_table][v.f_field] >= v.f_value
        elif v.f_op == '>':
            qry = db[v.f_table][v.f_field] > v.f_value
        elif v.f_op == '<=':
            qry = db[v.f_table][v.f_field] <= v.f_value
        elif v.f_op == '<':
            qry = db[v.f_table][v.f_field] < v.f_value
        else:
            return q
    if q is None:
        q = qry
    elif v.f_log_op == 'AND':
        q &= qry
    elif v.f_log_op == 'AND NOT':
        q &= ~qry
    elif v.f_log_op == 'OR':
        q |= qry
    elif v.f_log_op == 'OR NOT':
        q |= ~qry
    return q

