from gluon.dal import smart_query

def allowed_user_ids():
    """ Return ids of the users member of the same groups than the requester.
    """
    q = db.auth_membership.group_id.belongs(user_group_ids())
    rows = db(q).select(db.auth_membership.user_id)
    return [r.user_id for r in rows]

def allowed_user_ids_q():
    try:
        check_privilege("UserManager")
        q = db.auth_user.id > 0
    except:
        user_ids = allowed_user_ids()
        q = db.auth_user.id.belongs(user_ids)
    return q

def user_id_q(id):
    """ Return a DAL expression limiting the query to the users member of the same groups than the requester.
    """
    if type(id) in (unicode, str) and "@" in id:
        q = db.auth_user.email == id
    else:
        q = db.auth_user.id == id
    return q


#
class rest_get_users(rest_get_table_handler):
    def __init__(self):
        desc = [
          "List existing users.",
          "Managers and UserManager are allowed to see all users.",
          "Others can only see users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users?query=email contains opensvc",
        ]

        rest_get_table_handler.__init__(
          self,
          path="/users",
          tables=["auth_user"],
          props_blacklist=["password", "registration_key"],
          desc=desc,
          examples=examples,
        )

    def handler(self, **vars):
        q = allowed_user_ids_q()
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_get_user(rest_get_line_handler):
    def __init__(self):
        desc = [
          "Display user properties.",
          "Managers and UserManager are allowed to see all users.",
          "Others can only see users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s?props=lock_filter",
        ]
        rest_get_line_handler.__init__(
          self,
          path="/users/<id>",
          tables=["auth_user"],
          props_blacklist=["password", "registration_key"],
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        self.set_q(q)
        return self.prepare_data(**vars)

#
class rest_get_users_self(rest_get_line_handler):
    def __init__(self):
        desc = [
          "Display the logged-in user properties.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/self",
        ]
        rest_get_line_handler.__init__(
          self,
          path="/users/self",
          tables=["auth_user"],
          props_blacklist=["password", "registration_key"],
          desc=desc,
          examples=examples,
        )

    def handler(self, **vars):
        q = db.auth_user.id == auth.user_id
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_get_user_apps(rest_get_table_handler):
    def __init__(self):
        desc = [
          "List apps the user is responsible for.",
          "Managers and UserManager are allowed to see all users' information.",
          "Others can only see information for users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/apps",
        ]

        rest_get_table_handler.__init__(
          self,
          path="/users/<id>/apps",
          tables=["apps"],
          desc=desc,
          groupby=db.apps.id,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.apps_responsibles.group_id == db.auth_membership.group_id
        q &= db.auth_membership.user_id == db.auth_user.id
        q &= db.apps.id == db.apps_responsibles.app_id
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_get_user_nodes(rest_get_table_handler):
    def __init__(self):
        desc = [
          "List nodes the user is responsible of.",
          "Managers and UserManager are allowed to see all users' information.",
          "Others can only see information for users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/nodes",
        ]

        rest_get_table_handler.__init__(
          self,
          path="/users/<id>/nodes",
          tables=["nodes"],
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.nodes.team_responsible == db.auth_group.role
        q &= db.auth_group.id == db.auth_membership.group_id
        q &= db.auth_membership.user_id == db.auth_user.id
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_get_user_services(rest_get_table_handler):
    def __init__(self):
        desc = [
          "List services the user is responsible of.",
          "Managers and UserManager are allowed to see all users' information.",
          "Others can only see information for users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/services",
        ]
        rest_get_table_handler.__init__(
          self,
          path="/users/<id>/services",
          tables=["services"],
          groupby=db.services.id,
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.services.svc_app == db.apps.app
        q &= db.apps.id == db.apps_responsibles.app_id
        q &= db.apps_responsibles.group_id == db.auth_membership.group_id
        q &= db.auth_membership.user_id == db.auth_user.id
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_get_user_groups(rest_get_table_handler):
    def __init__(self):
        desc = [
          "List groups the user is member of.",
          "Managers and UserManager are allowed to see all users' information.",
          "Others can only see information for users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/groups",
        ]
        rest_get_table_handler.__init__(
          self,
          path="/users/<id>/groups",
          tables=["auth_group"],
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.auth_membership.user_id == db.auth_user.id
        q &= db.auth_group.id == db.auth_membership.group_id
        self.set_q(q)
        return self.prepare_data(**vars)

#
class rest_get_user_primary_group(rest_get_line_handler):
    def __init__(self):
        desc = [
          "Display the user's primary group properties.",
          "Managers and UserManager are allowed to see all users' information.",
          "Others can only see information for users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/primary_group",
        ]
        rest_get_line_handler.__init__(
          self,
          path="/users/<id>/primary_group",
          tables=["auth_group"],
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.auth_membership.user_id == db.auth_user.id
        q &= db.auth_membership.primary_group == True
        q &= db.auth_group.id == db.auth_membership.group_id
        self.set_q(q)
        return self.prepare_data(**vars)

#
class rest_post_users(rest_post_handler):
    def __init__(self):
        self.get_handler = rest_get_users()
        self.update_one_handler = rest_post_user()
        self.update_one_param = "email"

        desc = [
          "Create a user.",
          "Update users matching the specified query."
          "The user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -X POST -o- -d first_name=John -d last_name=Smith https://%(collector)s/init/rest/api/users",
        ]
        rest_post_handler.__init__(
          self,
          path="/users",
          tables=["auth_user"],
          desc=desc,
          examples=examples
        )

    def handler(self, **vars):
        check_privilege("UserManager")
        obj_id = db.auth_user.insert(**vars)
        _log('user.create',
             'add user %(data)s',
             dict(data=str(vars)),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return rest_get_user().handler(obj_id)


#
class rest_post_user(rest_post_handler):
    def __init__(self):
        desc = [
          "Modify a user properties.",
          "The user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X POST -d perpage=20 https://%(collector)s/init/rest/api/users/10",
        ]
        rest_post_handler.__init__(
          self,
          path="/users/<id>",
          tables=["auth_user"],
          desc=desc,
          examples=examples
        )

    def handler(self, id, **vars):
        check_privilege("UserManager")
        try:
            id = int(id)
            q = db.auth_user.id == id
        except:
            q = db.auth_user.email == id
        row = db(q).select().first()
        if row is None:
            return dict(error="User %s does not exist" % str(id))
        if "id" in vars.keys():
            del(vars["id"])
        db(q).update(**vars)
        l = []
        for key in vars:
            l.append("%s: %s => %s" % (str(key), str(row[key]), str(vars[key])))
        _log('user.change',
             'change user %(data)s',
             dict(data=', '.join(l)),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return rest_get_user().handler(row.id)


#
class rest_delete_user(rest_delete_handler):
    def __init__(self):
        desc = [
          "Delete a user.",
          "Delete all group membership.",
          "The user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the changed tables.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X DELETE https://%(collector)s/init/rest/api/users/10",
        ]

        rest_delete_handler.__init__(
          self,
          path="/users/<id>",
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        check_privilege("UserManager")
        try:
            id = int(id)
            q = db.auth_user.id == id
        except:
            q = db.auth_user.email == id

        row = db(q).select().first()
        if row is None:
            return dict(info="User %s does not exists" % str(id))

        # group
        db(q).delete()
        _log('user.delete',
             'deleted user %(email)s',
             dict(email=row.email))
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))

        # group membership
        q = db.auth_membership.user_id == row.id
        db(q).delete()

        return dict(info="User %s deleted" % row.email)

#
class rest_post_user_group(rest_post_handler):
    def __init__(self):
        desc = [
          "Attach a user to a group.",
          "The api user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X POST https://%(collector)s/init/rest/api/users/10/groups/10",
        ]
        rest_post_handler.__init__(
          self,
          path="/users/<id>/groups/<id>",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, group_id, **vars):
        check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user_id))

        try:
            id = int(id)
            q = db.auth_group.id == group_id
        except:
            q = db.auth_group.role == group_id
        group = db(q).select().first()
        if group is None:
            return dict(error="Group %s does not exist" % str(group_id))

        q = db.auth_membership.user_id == user.id
        q &= db.auth_membership.group_id == group.id
        q &= db.auth_membership.primary_group == 'F'
        row = db(q).select().first()
        if row is not None:
            return dict(info="User %s is already attached to group %s" % (str(user.email), str(group.role)))

        db.auth_membership.insert(user_id=user_id, group_id=group_id, primary_group='F')
        _log('user.group.attach',
             'user %(u)s attached to group %(g)s',
             dict(u=user.email, g=group.role),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s attached to group %s" % (str(user.email), str(group.role)))


#
class rest_delete_user_group(rest_delete_handler):
    def __init__(self):
        desc = [
          "Detach a user from a group.",
          "The api user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X DELETE https://%(collector)s/init/rest/api/users/10/groups/10",
        ]
        rest_delete_handler.__init__(
          self,
          path="/users/<id>/groups/<id>",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, group_id, **vars):
        check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user_id))

        try:
            id = int(id)
            q = db.auth_group.id == group_id
        except:
            q = db.auth_group.role == group_id
        group = db(q).select().first()
        if group is None:
            return dict(error="Group %s does not exist" % str(group_id))

        q = db.auth_membership.user_id == user.id
        q &= db.auth_membership.group_id == group.id
        q &= db.auth_membership.primary_group == 'F'
        row = db(q).select().first()
        if row is None:
            return dict(info="User %s is already detached from group %s" % (str(user.email), str(group.role)))

        db(q).delete()
        _log('user.group.detach',
             'user %(u)s detached from group %(g)s',
             dict(u=user.email, g=group.role),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s detached from group %s" % (str(user.email), str(group.role)))


#
class rest_post_user_primary_group(rest_post_handler):
    def __init__(self):
        desc = [
          "Set a user's primary group.",
          "The api user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X POST https://%(collector)s/init/rest/api/users/10/primary_group/10",
        ]
        rest_post_handler.__init__(
          self,
          path="/users/<id>/primary_group/<id>",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, group_id, **vars):
        check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user_id))

        try:
            id = int(id)
            q = db.auth_group.id == group_id
        except:
            q = db.auth_group.role == group_id
        group = db(q).select().first()
        if group is None:
            return dict(error="Group %s does not exist" % str(group_id))

        q = db.auth_membership.user_id == user.id
        q &= db.auth_membership.group_id == group.id
        q &= db.auth_membership.primary_group == 'T'
        row = db(q).select().first()
        if row is not None:
            return dict(info="User %s primary group is already %s" % (str(user.id), str(group.id)))

        q = db.auth_membership.user_id == user_id
        q &= db.auth_membership.primary_group == 'T'
        db(q).delete()
        db.auth_membership.insert(user_id=user.id, group_id=group.id, primary_group='T')
        _log('user.primary_group.attach',
             'user %(u)s primary group set to %(g)s',
             dict(u=user.email, g=group.role),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s primary group set to %s" % (str(user.email), str(group.role)))


#
class rest_delete_user_primary_group(rest_delete_handler):
    def __init__(self):
        desc = [
          "Unset a user's primary group.",
          "The api user must be in the UserManager privilege group.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X DELETE https://%(collector)s/init/rest/api/users/10/primary_group/10",
        ]
        rest_delete_handler.__init__(
          self,
          path="/users/<id>/primary_group",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, **vars):
        check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user.email))

        q = db.auth_membership.user_id == user.id
        q &= db.auth_membership.primary_group == 'T'
        row = db(q).select().first()
        if row is None:
            return dict(info="User %s has already no primary group" % str(user.email))

        db(q).delete()
        _log('user.primary_group.detach',
             'user %(u)s primary group unset',
             dict(u=user.email),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s primary group unset" % str(user.email))


#
class rest_get_user_filterset(rest_get_line_handler):
    def __init__(self):
        desc = [
          "Display the user's current filterset.",
          "Managers and UserManager are allowed to see all users' current filterset.",
          "Others can only see the current filterset of users in their organisational groups.",
        ]
        examples = [
          "# curl -u %(email)s -o- https://%(collector)s/init/rest/api/users/%(email)s/filterset",
        ]
        rest_get_line_handler.__init__(
          self,
          path="/users/<id>/filterset",
          tables=["gen_filtersets"],
          desc=desc,
          examples=examples,
        )

    def handler(self, id, **vars):
        q = allowed_user_ids_q()
        q &= user_id_q(id)
        q &= db.gen_filterset_user.user_id == db.auth_user.id
        q &= db.gen_filtersets.id == db.gen_filterset_user.fset_id
        self.set_q(q)
        return self.prepare_data(**vars)


#
class rest_post_user_filterset(rest_post_handler):
    def __init__(self):
        desc = [
          "Set a user's current filterset.",
          "The api user must be in the UserManager privilege group or the specified user himself.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X POST https://%(collector)s/init/rest/api/users/10/filterset/10",
        ]
        rest_post_handler.__init__(
          self,
          path="/users/<id>/filterset/<id>",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, fset_id, **vars):
        q = user_id_q(user_id)
        q &= db.auth_user.id == auth.user_id
        row = db(q).select().first()
        if row is None:
            check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user_id))

        try:
            id = int(id)
            q = db.gen_filtersets.id == fset_id
        except:
            q = db.gen_filtersets.fset_name == fset_id
        fset = db(q).select().first()
        if fset is None:
            return dict(error="Filterset %s does not exist" % str(fset_id))

        q = db.gen_filterset_user.user_id == user.id
        q &= db.gen_filterset_user.fset_id == fset.id
        row = db(q).select().first()
        if row is not None:
            return dict(info="User %s filterset is already %s" % (str(user.email), str(fset.fset_name)))

        q = db.gen_filterset_user.user_id == user.id
        db(q).delete()
        db.gen_filterset_user.insert(user_id=user.id, fset_id=fset.id)
        _log('user.filterset.attach',
             'user %(u)s filterset set to %(g)s',
             dict(u=user.email, g=fset.fset_name),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s filterset set to %s" % (str(user.email), str(fset.fset_name)))

#
class rest_delete_user_filterset(rest_delete_handler):
    def __init__(self):
        desc = [
          "Unset a user's current filterset.",
          "The api user must be in the UserManager privilege group or the specified user himself.",
          "The action is logged in the collector's log.",
          "A websocket event is sent to announce the change in the users table.",
        ]
        examples = [
          "# curl -u %(email)s -o- -X DELETE https://%(collector)s/init/rest/api/users/10/filterset",
        ]
        rest_delete_handler.__init__(
          self,
          path="/users/<id>/filterset",
          desc=desc,
          examples=examples
        )

    def handler(self, user_id, **vars):
        q = user_id_q(user_id)
        q &= db.auth_user.id == auth.user_id
        row = db(q).select().first()
        if row is None:
            check_privilege("UserManager")
        try:
            id = int(user_id)
            q = db.auth_user.id == user_id
        except:
            q = db.auth_user.email == user_id
        user = db(q).select().first()
        if user is None:
            return dict(error="User %s does not exist" % str(user_id))

        q = db.gen_filterset_user.user_id == user.id
        row = db(q).select().first()
        if row is None:
            return dict(info="User %s has already no filterset" % str(user.email))
        db(q).delete()
        _log('user.filterset.detach',
             'user %(u)s filterset unset',
             dict(u=user.email),
            )
        l = {
          'event': 'auth_user',
          'data': {'foo': 'bar'},
        }
        _websocket_send(event_msg(l))
        return dict(info="User %s filterset unset" % str(user.email))


