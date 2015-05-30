import logging
from object import ZabbixObject

log = logging.getLogger(__name__)


class ZabbixDiscovery(ZabbixObject):

    """
    Implements working with zabbix discovery objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix discovery template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        self.obj_type = 'discoveryrule'
        ZabbixObject(self.zapi, self.obj, self.template_id)

    def _create_request(self):
        """
        Create request for changes.

        Return  (str)   Request for changes.
        """

        result = None
        result = {
            'name': self.obj['name'],
            'key_': self.obj['key'],
            'description': self.obj.get('description'),
            'delay': self.obj.get(
                'interval',
                self.defaults['default']['discovery']['delay']),
            'lifetime': self.obj.get(
                'keep_days',
                self.defaults['default']['discovery']['lifetime']),
            'type': self.defaults['method'].index(
                self.obj.get(
                    'method',
                    'agent').lower()),
            'hostid': self.template_id,
            'status': int(
                bool(
                    self.obj.get(
                        'disabled',
                        self.defaults['default']['disabled']))),
            'filter': "{0}:{1}".format(
                self.obj.get(
                    'filter',
                    {}).get('macro'),
                self.obj.get(
                    'filter',
                    {}).get('regexp')),
        }
        return result
