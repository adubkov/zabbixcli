import logging
from group import ZabbixGroups
from object import ZabbixObject

# Connect to logger object
log = logging.getLogger(__name__)


class ZabbixTriggerAction(ZabbixObject):

    """
    Implements working with zabbix trigger action objects.

    Arguments:
    zapi  (ZabbixAPI)   ZabbixAPI connector to send request.
    obj   (dict)        Dictionary discribed zabbix application template.
    """

    def __init__(self, zapi, obj, defaults, template_id, template_name):
        self.zapi = zapi
        self.obj = obj
        self.obj_type = 'action'
        self.defaults = defaults
        self.template_id = template_id
        self.template_name = template_name
        ZabbixObject(self.zapi, self.obj)

    def _create_request(self):
        """
        Create request for changes.

        Return  (str)   Request for changes.
        """

        result = {}

        if self.obj:
            result['name'] = '{0}: {1}'.format(self.template_name, self.obj['name'])
            result['def_shortdata'] = self.obj.get('subject',
                    self.defaults['default']['alert']['subject'])
            result['def_longdata'] = self.obj.get('text',
                    self.defaults['default']['alert']['text'])

            if bool(
                self.obj.get(
                    'recovery',
                    self.defaults['default']['alert']['recovery'])):
                result['recovery_msg'] = 1
                result['r_shortdata'] = self.obj.get('recovery_subject',
                        self.defaults['default']['alert']['recovery_subject'])
                result['r_longdata'] = self.obj.get('recovery_text',
                        self.defaults['default']['alert']['recovery_text'])

            result['eventsource'] = self.defaults[
                'default']['alert']['eventsource']
            result['status'] = int(
                bool(
                    self.obj.get(
                        'disabled',
                        self.defaults['default']['disabled'])))
            result['esc_period'] = self.obj.get(
                'escalation_time',
                self.defaults['default']['alert']['escalation_time'])
            result['evaltype'] = self.obj.get(
                'eval',
                self.defaults['default']['alert']['eval'])

            alert_severity = self.defaults['warn_level'].index(
                self.obj.get(
                    'severity',
                    self.defaults['default']['alert']['warn_level']).lower())
            alert_severity_cmp = self.defaults['cmp'][
                self.obj.get(
                    'severity_cmp',
                    self.defaults['default']['alert']['cmp']).lower()]
            alert_trigger_status = self.defaults['trigger_status'].index(
                self.obj.get(
                    'trigger_status',
                    self.defaults['default']['alert']['trigger_status']).lower())

            result['conditions'] = [
                # actionid: Mainenance status - 16, not in - 7
                {'conditiontype': 16, 'operator': 7},
                # actionid: Trigger value - 5, equal - 0, PROBLEM - 1
                {'conditiontype': 5,
                 'operator': 0,
                 'value': alert_trigger_status},
                # actionid: Trigger severity - 4, equal - 0, Warning - 2
                {'conditiontype': 4,
                 'operator': alert_severity_cmp,
                 'value': alert_severity},
            ]

            if 'group' in self.obj:
                result['conditions'].append({
                    'conditiontype': 0,
                    'operator': 0,
                    'value': self.zapi.get_id(
                        'hostgroup',
                        self.obj['group'])
                    })
            elif not 'all' in self.obj:
                # actionid: Template - 13, like - 2
                result['conditions'].append({
                    'conditiontype': 13,
                    'operator': 0,
                    'value': self.template_id})

            result['operations'] = []

            # fill operations for alert
            for op in self.obj.get('do', []):
                # check if we need to send a message to user or group
                if op.get(
                        'action',
                        self.defaults['default']['alert']['action']) == 'message':
                    # basic config for message
                    do_obj = {
                        'operationtype': 0,
                        'esc_step_to': 1,
                        'esc_step_from': 1,
                        'esc_period': 0,
                        'evaltype': 0,
                    }
                    do_obj.update(
                        {
                            'opmessage': {
                                'mediatypeid': self.zapi.get_id(
                                    'mediatype',
                                    op.get(
                                        'over',
                                        self.defaults['default']['alert']['over'])),
                                'default_msg': 1,
                            }})

                    if op.get('to_user'):
                        do_obj.update(
                            {'opmessage_usr': [self.zapi.get_id('user', op['to_user'], with_id=True)]})

                    if op.get('to_group'):
                        do_obj.update(
                            {'opmessage_grp': [self.zapi.get_id('usergroup', op['to_group'], with_id=True)]})

                    result['operations'].append(do_obj)
                # TODO: elif = 'exec' ... run

        return result

    def apply(self):
        """
        Push action object to zabbix server.
        """

        result = None
        req = self._create_request()

        log.info("%s: '%s'", str(self.obj_type).capitalize(), req['name'])

        # Get 'action' object id
        log.debug(
            'ZabbixTriggerAction._create_request: {req}'.format(
                req=req))
        obj_id = self.zapi.get_id('action', req['name'])

        if obj_id:
            req['actionid'] = obj_id
            req.pop('name')
            obj_action = 'update'
        else:
            obj_action = 'create'

        func = 'self.zapi.{obj_type}.{obj_action}'.format(
            obj_type=self.obj_type,
            obj_action=obj_action)
        result = eval(func)(req)

        return result
