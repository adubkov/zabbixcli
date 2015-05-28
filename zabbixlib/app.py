import logging
from object import ZabbixObject

# Connect to logger object
logger = logging.getLogger(__name__)


class ZabbixApp(ZabbixObject):

    """
    Implements working with zabbix application objects.

    Arguments:
    zapi  (ZabbixAPI)   ZabbixAPI connector to send request.
    obj   (dict)        Dictionary discribed zabbix application template.
    """

    def __init__(self, zapi, obj, template_id):
        self.zapi = zapi
        self.obj = obj
        self.template_id = template_id
        self.obj_type = 'application'
        ZabbixObject(self.zapi, self.obj)

    def push(self):
        """
        Push application object to zabbix server.
        """
        result = None

        # Get 'application' object id
        obj_id = self.zapi.get_id(
            'application',
            self.obj,
            hostid=self.template_id)

        if obj_id:
            result = obj_id
        else:
            app = {
                'name': self.obj,
                'hostid': self.template_id
            }

            logger.debug('call: sync_app({name}, {hostid})'.format(**app))
            result = self.zapi.application.create(app)
            result = result['applicationids'][0]
        return result
