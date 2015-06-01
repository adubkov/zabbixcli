import logging
from object import ZabbixObject

log = logging.getLogger(__name__)


class ZabbixItem(ZabbixObject):

    """
    Implements working with zabbix item objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix item template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj=None, defaults=None, template_id=None):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        self.obj_type = 'item'
        ZabbixObject(self.zapi, self.obj, self.template_id)

    def _create_request(self):
        """
        Create request for item changes.

        Return  (str)   Request for changes.
        """

        value_type = self.defaults['return_type'].index(
            self.obj.get(
                'return_type',
                'numeric').lower())
        status = int(
            bool(
                self.obj.get(
                    'disabled',
                    self.defaults['default']['disabled'])))
        delay = int(
            self.obj.get(
                'interval',
                self.defaults['default']['item']['interval']))
        history = int(
            self.obj.get(
                'history',
                self.defaults['default']['item']['history']))
        trends = int(
            self.obj.get(
                'trends',
                self.defaults['default']['item']['trends']))
        type_ = self.defaults['method'].index(
            self.obj.get(
                'method',
                self.defaults['default']['item']['method']).lower())
        delta = self.defaults['store_as'].index(
            self.obj.get(
                'store_as',
                self.defaults['default']['item']['store_as']).lower())

        result = {
            'name': self.obj['name'],
            'type': type_,
            'key_': self.obj['key'],
            'value_type': value_type,
            'status': status,
            'applications': [self.obj.get('app_id')],
            'hostid': self.template_id,
            'delay': delay,
            'history': history,
            'trends': trends,
            'description': self.obj.get('description', ''),
            'delta': delta,
        }

        if 'params' in self.obj:
            result.update({'params': self.obj['params']})

        if self.obj.get(
                'return_type',
                'numeric').lower() != 'boolean' and self.obj.get('units'):
            result.update({
                'units': self.obj.get('units'),
                'multiplier': int(bool(self.obj.get('multiplier', 0))),
                'formula': self.obj.get('multiplier', 0),
            })
        return result

    def disable(self, id_):
        """
        Disable specifiec zabbix item.

        Arguments:
        id_   (int)     Zabbix item ID.
        """

        return self.zapi.item.update({'itemid': id_, 'status': 1})


class ZabbixItemPrototype(ZabbixItem):

    """
    Implements working with zabbix item prototype objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix item template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        ZabbixItem(self.zapi, self.obj, self.defaults, self.template_id)

    def _create_request(self):
        """
        Create request for item prototype changes.

        Return  (str)   Request for changes.
        """

        result = None
        result = super(ZabbixItemPrototype, self)._create_request()
        result.update({'ruleid': self.obj.get('rule_id')})
        self.obj_type = 'itemprototype'
        return result
