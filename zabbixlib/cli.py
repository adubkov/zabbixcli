import fcntl
import json
import logging
import struct
import sys
import termios
import os

try:
    import argparse
except:
    raise Exception(
        "You need python version 2.7+ or installed argparse module")

from app import ZabbixApp
from autoreg import ZabbixAutoreg
from defaults import ZabbixDefaults
from discovery import ZabbixDiscovery
from group import ZabbixGroup
from graph import ZabbixGraph, ZabbixGraphPrototype
from item import ZabbixItem, ZabbixItemPrototype
from macro import ZabbixMacro
from object import ZabbixObject
from template import ZabbixTemplate, ZabbixTemplateFile
from trigger import ZabbixTrigger, ZabbixTriggerPrototype
from trigger_action import ZabbixTriggerAction
from zabbix.api import ZabbixAPI

# Connect to logger object
logger = logging.getLogger(__name__)


class ZabbixCLIArguments(object):

    """
    Manage zabbixcli arguments
    """

    def __init__(self):
        # Create arguments perser object
        self.argparser = argparse.ArgumentParser(
            description='Template based zabbix configuration tool')
        self.args = {}
        self._loadFromEnvironment()
        self._parse()

    def _loadFromEnvironment(self):
        """
        Load arguments from enviroment variables
        """

        # Map env variables to cli arguments
        args_map = {
            'ZBXCLI_USER': 'user',
            'ZBXCLI_PASS': 'pass',
            'ZBXCLI_URL': 'server'}

        # Load env variables
        for ev, arg in args_map.iteritems():
            if ev in os.environ:
                self.args[arg] = os.environ[ev]

    def _parse(self):
        """
        Parse CLI arguments into self.args
        """

        # Add arguments
        self.argparser.add_argument(
            '-t',
            '--template',
            action='store',
            type=str,
            help='Template name for sync')
        self.argparser.add_argument(
            '-s',
            '--server',
            action='store',
            type=str,
            help='Zabbix server URL')
        self.argparser.add_argument(
            '-u',
            '--user',
            action='store',
            type=str,
            help='Zabbix user name')
        self.argparser.add_argument(
            '-p',
            '--pass',
            action='store',
            type=str,
            help='Zabbix user password')
        self.argparser.add_argument(
            '-o',
            '--only',
            action='store_true',
            help='Sync only specified templates')
        self.argparser.add_argument(
            '-d',
            '--debug',
            action='store_true',
            help='Enable debug mode')
        self.argparser.add_argument(
            '-D',
            '--delete',
            action='store',
            type=str,
            nargs='+',
            help='Delete object from zabbix. Example: -D item "Template OS Linux" "Available memory"')

        # Updage arguments from CLI
        self.args.update(
            # filter out Null arguments
            filter(
                lambda x: x[1],
                vars(
                    # Parse arguments
                    self.argparser.parse_args()).items()))


class ProgressBar(object):

    """
    Draw a progress bar in terminal
    """

    def __init__(self, obj):
        self.w, self.h = self._getTerminalSize()
        self.obj = obj
        self.obj_len = len(self.obj)

    def _getTerminalSize(self):
        """
        Return current terminal Height and Width in chars
        """

        if os.isatty(0):
            # Create parameter
            param = struct.pack('HHHH', 0, 0, 0, 0)
            # Get terminal info
            op_result = fcntl.ioctl(0, termios.TIOCGWINSZ, param)
            # Unpack result data
            h, w, hp, wp = struct.unpack('HHHH', op_result)
        else:
            w, h = 80, 40
        return w, h

    def _progressbar_update(self):
        """
        Update progressbar state
        """

        self.obj.processed_items += 1
        # calculate count of #
        self.x = self.w - 8 - (len(str(self.obj_len)) * 2)
        # calculate shift of #
        self.y = int(self.x / float(self.obj_len) * self.obj.processed_items)
        # update screen
        self._print()

    def _print(self):
        """
        Print progressbar state on screen
        """

        s = '\r [{0:#>{3}}] {1}/{2}\r'.format(
            ' ' * (self.x - self.y), self.obj.processed_items, self.obj_len, self.x)
        sys.stdout.write(s)
        # if EOL write \n
        if self.y == self.x:
            sys.stdout.write('\n')
        # flush buffer to screen
        sys.stdout.flush()


class ZabbixCLI(ZabbixCLIArguments, ProgressBar):

    def __init__(self, template=None):
        ZabbixCLIArguments.__init__(self)

        # Set logging level
        if self.args.get('debug'):
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p')

        logger.debug('Parser arguments: %s', self.args)

        # if no arguments - print help
        if len(sys.argv) <= 1:
            self.argparser.print_help()
            sys.exit()

        if not self.args.get('template'):
            sys.exit('Template should be specified.')

        self.url = self.args['server']
        try:
            self.zapi = ZabbixAPI(
                self.url,
                user=self.args['user'],
                password=self.args['pass'])
        except:
            pass

        # If need to delete some object and exit
        if self.args.get('delete'):
            # type template item
            template_id = self.zapi.get_id('template', self.args['delete'][1])
            if ZabbixObject(self.zapi,
                            {'name': self.args['delete'][2]},
                            template_id=template_id,
                            obj_type=self.args['delete'][0]).delete():
                print '"{2}" {0} was deleted from "{1}"'.format(*self.args['delete'])
            else:
                print 'Error while trying to delete: "{2}" {0} from "{1}"'.format(*self.args['delete'])
            exit()

        if template:
            self.template_name = template
        else:
            self.template_name = self.args.get('template')

        self.template = ZabbixTemplateFile(self.template_name)
        self.template_id = None

        if self.template:
            self.config = ZabbixDefaults()
            ProgressBar.__init__(self, self.template)

            # Start pushing process
            self.push()

    def _push_linked_templates(self):
        if self.template.get('templates') and not self.args.get('only', False):
            print self.template.get('name') + ' depends from:'
            for linked_template in self.template.get('templates', []):
                print "\t{0}".format(linked_template)
            for linked_template in self.template.get('templates', []):
                ZabbixCLI(template=linked_template)

    def _push_template(self, template):
        result = None
        print('Syncing : {0}'.format(template['name']))
        result = ZabbixTemplate(self.zapi, template).push()
        self._progressbar_update()
        return result

    def _push_macro(self, macro):
        result = None
        result = ZabbixMacro(self.zapi, macro, self.template_id).push()
        self._progressbar_update()
        return result

    def _push_macros(self):
        for macro in self.template.get('macros', []):
            self._push_macro(macro)

    def _push_app(self, app):
        result = None
        result = ZabbixApp(self.zapi, app, self.template_id).push()
        self._progressbar_update()
        return result

    def _push_item(self, item):
        result = None
        result = ZabbixItem(
            self.zapi,
            item,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_items(self, items, app_id):
        for item in items:
            item['app_id'] = app_id
            self._push_item(item)

    def _push_item_prototype(self, prototype):
        result = None
        result = ZabbixItemPrototype(
            self.zapi,
            prototype,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_item_prototypes(self, discovery, app_id):
        items = discovery.get('items', [])
        rule_id = self.zapi.get_id(
            'discoveryrule',
            discovery['name'],
            templateid=self.template_id)
        for item in items:
            item.update({'rule_id': rule_id, 'app_id': app_id})
            self._push_item_prototype(item)

    def _push_graph(self, graph):
        result = None
        result = ZabbixGraph(
            self.zapi,
            graph,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_graphs(self):
        for graph in self.template.get('graphs', []):
            self._push_graph(graph)

    def _push_graph_prototype(self, prototype):
        result = None
        result = ZabbixGraphPrototype(
            self.zapi,
            prototype,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_graph_prototypes(self, discovery):
        graphs = discovery.get('graphs', [])
        for graph in graphs:
            self._push_graph_prototype(graph)

    def _push_trigger(self, trigger):
        result = None
        result = ZabbixTrigger(
            self.zapi,
            trigger,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_triggers(self):
        for trigger in self.template.get('triggers', []):
            self._push_trigger(trigger)

    def _push_trigger_prototype(self, prototype):
        result = None
        result = ZabbixTriggerPrototype(
            self.zapi,
            prototype,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_trigger_prototypes(self, discovery):
        triggers = discovery.get('triggers', [])
        for triggers in triggers:
            self._push_trigger_prototype(triggers)

    def _push_autoreg(self):
        result = None
        autoreg = self.template.get('autoreg')
        if autoreg:
            result = ZabbixAutoreg(self.zapi, self.template).push()
            self._progressbar_update()

    def _push_trigger_action(self):
        result = None
        alert = self.template.get('alert')
        if alert:
            result = ZabbixTriggerAction(
                self.zapi,
                self.template,
                self.config,
                self.template_id).push()
            self._progressbar_update()
        return result

    def _push_discovery(self, discovery):
        result = None
        result = ZabbixDiscovery(
            self.zapi,
            discovery,
            self.config,
            self.template_id).push()
        self._progressbar_update()
        return result

    def _push_discoveries(self):
        discoveries = self.template.get('discovery', {})

        for app, discovery in discoveries.iteritems():
            app_id = self._push_app(app)
            self._push_discovery(discovery)
            self._push_item_prototypes(discovery, app_id)
            self._push_graph_prototypes(discovery)
            self._push_trigger_prototypes(discovery)

    def _disable_item(self, id_):
        result = None
        result = ZabbixItem(self.zapi).disable(id_)
        return result

    def _disable_app(self, app):
        items = self.zapi.get_id(
            'item',
            None,
            hostid=self.template_id,
            app_name=app)
        for item in items:
            self._disable_item(item)

        self._progressbar_update()

    def push(self):
        self._push_linked_templates()
        self.template_id = self._push_template(self.template)

        # Push apps
        apps = self.template.get('applications', {})

        for app, items in apps.iteritems():
            # check if disabled whole app
            if str(items).lower() == 'disabled':
                self._disable_app(app)
            else:
                app_id = self._push_app(app)
                self._push_items(items, app_id)

        self._push_macros()
        self._push_graphs()
        self._push_triggers()
        self._push_discoveries()
        self._push_autoreg()
        self._push_trigger_action()
