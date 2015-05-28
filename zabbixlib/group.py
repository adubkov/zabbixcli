import logging

logger = logging.getLogger(__name__)


class ZabbixGroup(object):

    """
    Implements working with zabbix hostgroup\group objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    group       (str)             Group name.
    with_id     (bool)            Return values in zabbix format.
    """

    def __init__(self, zapi, group, with_id=False):
        self.zapi = zapi
        self.group = group
        self.with_id = with_id
        self.obj_type = 'hostgroup'

    def push(self):
        """
        Push hostgroup\group object to zabbix server.
        """

        result = None
        result = self.zapi.get_id('hostgroup', self.group)
        if not result:
            result = int(
                self.zapi.hostgroup.create(
                    name=self.group)['groupids'][0])
        if self.with_id:
            result = {'groupid': result}
        return result


class ZabbixGroups(object):

    """
    Implements working with zabbix hostgroups\groups objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    groups      (list of str)     List of group names.
    """

    def __init__(self, zapi, groups):
        self.zapi = zapi
        self.groups = groups

    def push(self):
        """
        Push hostgroups\groups object to zabbix server.
        """

        result = []
        for group in self.groups:
            groupid = ZabbixGroup(self.zapi, group, with_id=True).push()
            if groupid:
                result.append(groupid)
        return result