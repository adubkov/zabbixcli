import logging
from object import ZabbixObject

log = logging.getLogger(__name__)


class ZabbixMacro(ZabbixObject):

    """
    Implements working with zabbix usermacro objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix usermacro template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, template_id):
        self.zapi = zapi
        self.obj = obj
        self.template_id = template_id
        self.obj_type = 'usermacro'
        ZabbixObject(self.zapi, self.obj, self.template_id)

    def _create_request(self):
        """
        Create request for usermacro changes.

        Return  (str)   Request for changes.
        """

        result = None
        result = {
            'macro': self.obj['macro'],
            'value': self.obj['value'],
            'hostid': self.template_id,
        }
        return result

    def apply(self):
        """
        Push usermacro object to zabbix server.
        """
        result = None
        req = self._create_request()

        log.info("%s: '%s'", str(self.obj_type).capitalize(), req['macro'])

        # Get 'macro' object id
        log.debug('ZabbixMacro._create_request: %s', req)
        obj_id = self.zapi.get_id(
            'usermacro',
            req['macro'],
            hostid=self.template_id)

        if obj_id:
            result = self.zapi.usermacro.update(
                hostmacroid=obj_id,
                value=req['value'])
        else:
            result = self.zapi.usermacro.create(req)
        return result
