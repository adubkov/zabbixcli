import logging
from object import ZabbixObject

log = logging.getLogger(__name__)


class ZabbixTrigger(ZabbixObject):

    """
    Implements working with zabbix trigger objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix trigger template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        self.obj_type = 'trigger'
        ZabbixObject(self.zapi, self.obj, self.template_id)

    def _create_request(self):
        """
        Create request for trigger changes.

        Return  (str)   Request for changes.
        """

        result = None
        result = {
            # In trigger objects 'description' = 'name'
            'description': self.obj['name'],
            'expression': self.obj['expression'],
            'status': int(bool(self.obj.get('disabled', self.defaults['default']['disabled']))),
            'priority': self.defaults['warn_level'].index(self.obj.get('warn_level', self.defaults['default']['trigger']['warn_level']).lower()),
            'type': int(bool(self.obj.get('multiple_warn', self.defaults['default']['trigger']['multiple_warn']))),
            'url': self.obj.get('url', ''),
        }
        return result


class ZabbixTriggerPrototype(ZabbixTrigger):

    """
    Implements working with zabbix trigger prototype objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix trigger prototype template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        ZabbixTrigger(self.zapi, self.obj, self.defaults, self.template_id)

    def _create_request(self):
        """
        Create request for trigger changes.

        Return  (str)   Request for changes.
        """

        result = None
        result = super(ZabbixTriggerPrototype, self)._create_request()
        self.obj_type = 'triggerprototype'
        return result
