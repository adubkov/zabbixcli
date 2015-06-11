import pprint


class ZabbixDefaults(dict):

    """
    Store default values for zabbix settings, and map template names to zabbix id

    Example:
      # Override defaults
      c = ZabbixDefauls(disabled=True, item={'interval': 100})
    """

    def __init__(self, **args):
        # Return value constant
        self.__dict__['return_type'] = (
            'float',
            'char',
            'log',
            'numeric',
            'text')

        # Checking method constants
        self.__dict__['method'] = ('agent', 'snmp v1', 'trapper',
                                   'simple', 'snmp v2', 'internal', 'snmp v3',
                                   'active', 'aggregate', '', 'external',
                                   'database monitor', 'ipmi', 'ssh', 'telnet',
                                   'calculated', 'jmx', 'snmp trap')

        self.__dict__['store_as'] = ('as is', 'speed', 'change')

        # Graph constants
        self.__dict__['graph_type'] = ('normal', 'stacked', 'pie', 'exploded')
        self.__dict__['graph_y_type'] = ('calculated', 'fixed', 'item')
        self.__dict__['graph_func'] = {
            'min': 1,
            'avg': 2,
            'max': 4,
            'all': 7,
            'last': 9}
        self.__dict__['graph_style'] = ('line', 'filled region', 'bold line',
                                        'dot', 'dashed line', 'gradient line')
        self.__dict__['y_min_max_type'] = ('calculated', 'fixed', 'item')

        # Trigger severety level constants
        self.__dict__['warn_level'] = (
            'none',
            'info',
            'warning',
            'average',
            'high',
            'disaster')

        # Comparsion, for severety use in alerts
        self.__dict__['cmp'] = {'=': 0, '!=': 1, '>=': 5, '<=': 6}

        # Trigger status, for alerts
        self.__dict__['trigger_status'] = ('ok', 'problem')

        # Default parameters
        self.__dict__['default'] = {
            'disabled': False,
            'item': {
                'return_type': 'numeric',
                'method': 'agent',
                'interval': 60,
                'history': 7,
                'trends': 365,
                'store_as': 'as is',
            },
            'trigger': {
                'warn_level': 'none',
                'multiple_warn': False,
            },
            'graph': {
                'height': 200,
                'width': 900,
                'type': 'normal',
                'func': 'avg',
                'color': '009900',
                'y_side': 'left',
                'style': 'line',
                'gitype': 'simple',
                '3d_view': 0,
                'show_legend': 1,
                'show_working_time': 0,
                'show_triggers': 0,
                'y_min_type': 'calculated',
                'y_max_type': 'calculated',
                'percent_right': 0.0,
                'percent_left': 0.0,
            },
            'discovery': {
                'delay': 3600,
                'lifetime': 30,
            },
            'alert': {
                'recovery': True,
                'trigger_status': 'problem',
                'warn_level': 'warning',
                'subject': '[{EVENT.ID}] {TRIGGER.STATUS}: {TRIGGER.NAME} on {HOST.NAME1}',
                'text': ("{TRIGGER.SEVERITY}:\n"
                         "{TRIGGER.DESCRIPTION}\n"
                         "{HOST.NAME1}:[{ITEM.NAME1}]: {ITEM.VALUE1}"),
                'recovery_subject': '[{EVENT.ID}] {TRIGGER.STATUS}: {TRIGGER.NAME} on {HOST.NAME1}',
                'recovery_text': ("{TRIGGER.SEVERITY}:\n"
                                  "{TRIGGER.DESCRIPTION}\n"
                                  "{HOST.NAME1}:[{ITEM.NAME1}]: {ITEM.VALUE1}"),
                'eventsource': 0,       # Trigger handle
                'eval': 0,              # AND/OR: 0, AND: 1, OR: 2
                'escalation_time': 300,  # Must be >60s
                'over': 'Email',          # Email: 1
                'action': 'message',
                'cmp': '>=',
            },
        }

        # Override settings with argumentsi
        for k, v in args.iteritems():
            if isinstance(v, dict):
                self.__dict__['default'][k].update(v)
            else:
                self.__dict__['default'][k] = v

    def __getitem__(self, item):
        return self.__dict__.get(item)

    def get(self, item):
        return self.__getitem__(item)

    def __repr__(self):
        pf = pprint.PrettyPrinter(indent=4).pformat
        return pf(self.__dict__)
