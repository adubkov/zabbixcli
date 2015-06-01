import logging

log = logging.getLogger(__name__)


class ZabbixObject(object):

    """
    Base class for all zabbix objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix template.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, template_id=None, obj_type=None):
        self.zapi = zapi
        self.obj = obj
        self.template_id = template_id
        self.obj_type = obj_type

    def _get_id_name(self):
        """
        Return id name by object type (Zabbix use different name for id).
        """

        result = None
        id_name = {'discoveryrule': 'item',
                   'hostgroup': 'group',
                   'graphptototype': 'graph',
                   'itemprototype': 'item',
                   'triggerprototype': 'trigger',
                   }.get(self.obj_type, self.obj_type)
        result = '{0}id'.format(id_name)
        return result

    def _func(self, req):
        """
        Generate zapi function name.
        """

        result = None
        if self.template_id:
            obj_id = self.zapi.get_id(
                self.obj_type,
                self.obj['name'],
                hostid=self.template_id)
        if obj_id:
            req.update({self._get_id_name(): obj_id})
            zbx_method = 'update'
        else:
            zbx_method = 'create'

        result = "self.zapi.{obj_type}.{zbx_method}".format(
            obj_type=self.obj_type,
            zbx_method=zbx_method)

        return result

    def apply(self):
        """
        Push this object to zabbix server.
        """

        result = None
        req = self._create_request()
        log.info(
                "%s: '%s'",
                str(self.obj_type).capitalize(),
                self.obj.get('name'))
        func = self._func(req)
        log.debug('%s: %s', func, req)
        result = eval(func)(req)

        return result

    def delete(self):
        """
        Delete this object from zabbix.
        """

        result = None
        obj_id = self.zapi.get_id(self.obj_type, self.obj['name'])
        if obj_id:
            func = 'self.zapi.{obj_type}.delete'.format(obj_type=self.obj_type)
            result = eval(func)(obj_id)

        return result
