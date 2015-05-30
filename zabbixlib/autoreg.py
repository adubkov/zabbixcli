import logging
from group import ZabbixGroups
from object import ZabbixObject

# Connect to logger object
log = logging.getLogger(__name__)


class ZabbixAutoreg(ZabbixObject):

    """
    Implements working with zabbix autoregister action objects.

    Arguments:
    zapi  (ZabbixAPI)   ZabbixAPI connector to send request.
    obj   (dict)        Dictionary discribed zabbix application template.
    """

    def __init__(self, zapi, obj):
        self.zapi = zapi
        self.obj = obj
        self.obj_type = 'action'
        ZabbixObject(self.zapi, self.obj)

    def _create_request(self):
        """
        Create request for changes.

        Return  (str)   Request for changes.
        """

        result = {}
        result['name'] = 'Auto registration {role}'.format(
            role=self.obj['name'])

        # if contains metadata tag then use it
        if isinstance(
                self.obj['autoreg'],
                dict) and self.obj['autoreg'].get('metadata'):
            metadata = self.obj['autoreg']['metadata']
        else:
            metadata = self.obj['name']

        result['conditions'] = [
            # actionid: host metadata - 24, like - 2
            {'conditiontype': 24, 'operator': 2, 'value': metadata}
        ]

        result['operations'] = [
            {
                # actionid: link template - 6
                'operationtype': 6, 'esc_step_to': 1, 'esc_step_from': 1, 'esc_period': 0,
                'optemplate': [self.zapi.get_id('template', self.obj['name'], with_id=True)],
            },
            # Add host
            {'esc_step_from': 1,
             'esc_period': 0,
             'operationtype': 2,
             'esc_step_to': 1},
            # Disable host
            {'esc_step_from': 1,
             'esc_period': 0,
             'operationtype': 9,
             'esc_step_to': 1},
        ]

        # if contains add_to_group
        if isinstance(
                self.obj['autoreg'],
                dict) and self.obj['autoreg'].get('add_to_group'):
            result['operations'].append(
                {
                    # actionid: add to hostgroup - 4
                    'operationtype': 4, 'esc_step_to': 1, 'esc_step_from': 1, 'esc_period': 0,
                    'opgroup': ZabbixGroups(
                        self.zapi,
                        self.obj.get('autoreg')['add_to_group']).apply()
                },
            )
        return result

    def apply(self):
        """
        Push action object to zabbix server.
        """

        result = None
        req = self._create_request()

        log.info("Auto-registration: '%s'", req['name'])

        # Get 'action' object id
        log.debug('ZabbixAutoreg._create_request: %s', req)
        obj_id = self.zapi.get_id('action', req['name'])

        if obj_id:
            result = self.zapi.action.update(
                actionid=obj_id,
                eventsource=2,
                status=0,
                esc_period=0,
                evaltype=0,
                conditions=req['conditions'],
                operations=req['operations'])
        else:
            result = self.zapi.action.create(
                name=req['name'],
                eventsource=2,
                status=0,
                esc_period=0,
                evaltype=0,
                conditions=req['conditions'],
                operations=req['operations'])
        return result
