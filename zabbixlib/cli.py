import collections
import json
import logging
import sys
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
log = logging.getLogger(__name__)


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
            'ZBXCLI_URL': 'server',
            'ZBXCLI_TEMPLATES': 'templates_dir',}

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


class ZabbixCLI(ZabbixCLIArguments):

    def __init__(self, template=None):
        ZabbixCLIArguments.__init__(self)
        self._configureLogging()
        log.debug('Parser arguments: %s', self.args)

        # if no arguments, jsut print help
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
            log.error('Error while trying open connection to zabbix server: %s',
                    self.url)

        # If we need to delete an object and exit
        if self.args.get('delete'):
            template_id = self.zapi.get_id('template', self.args['delete'][1])
            if ZabbixObject(self.zapi,
                            {'name': self.args['delete'][2]},
                            template_id=template_id,
                            obj_type=self.args['delete'][0]).delete():
                log.info(
                    '"{2}" {0} was deleted from "{1}"'.format(
                        *self.args['delete']))
            else:
                log.exit(
                    'Error while trying to delete: "{2}" {0} from "{1}"'.format(
                        *self.args['delete']))
            exit()

        # Set template name from __init__ params or args
        if template:
            self.template_name = template
        else:
            self.template_name = self.args.get('template')

        # Load template from file
        self.template = ZabbixTemplateFile(self.template_name, templates_dir=self.args.get('templates_dir'))
        self.template_id = None

        # When template loaded, set defaults and run apply process
        if self.template:
            self.config = ZabbixDefaults()
            self.apply()

    def _configureLogging(self):
        """
        Configure logging output. Format and colors.
        """

        # Set logging level
        if self.args.get('debug'):
            logLevel = logging.DEBUG
        else:
            logLevel = logging.INFO

        # Set colored output
        colors = {'reset': '\033[0m', 'green': '\x1b[32m', 'cyan': '\x1b[36m'}
        logFormat = '{reset}{cyan}[{green}%(asctime)s{cyan}]{reset} %(message)s'.format(
            **colors)
        logging.basicConfig(
            level=logLevel,
            format=logFormat,
            datefmt='%d/%m/%Y %H:%M:%S')

    def _apply_linked_templates(self):
        """
        Recursive apply list of linked templates. They will applied before main
        template will start applying.
        """

        if self.template.get('templates') and not self.args.get('only', False):
            log.info('%s depends from:', self.template.get('name'))
            # Show linked template list before applying
            for linked_template in self.template.get('templates', []):
                log.info("\t\t%s", linked_template)
            # Apply list of linked templates
            for linked_template in self.template.get('templates', []):
                ZabbixCLI(template=linked_template)

    def _apply_template(self, template):
        ZabbixTemplate(self.zapi, template).apply()

    def _apply_macro(self, macro):
        ZabbixMacro(self.zapi, macro, self.template_id).apply()

    def _apply_macros(self):
        for macro in self.template.get('macros', []):
            self._apply_macro(macro)

    def _apply_app(self, app):
        ZabbixApp(self.zapi, app, self.template_id).apply()

    def _apply_item(self, item):
        ZabbixItem(self.zapi, item, self.config, self.template_id).apply()

    def _apply_items(self, items, app_id):
        for item in items:
            item['app_id'] = app_id
            self._apply_item(item)

    def _apply_item_prototype(self, prototype):
        ZabbixItemPrototype(self.zapi, prototype, self.config, self.template_id).apply()

    def _apply_item_prototypes(self, discovery, app_id):
        items = discovery.get('items', [])
        rule_id = self.zapi.get_id(
            'discoveryrule',
            discovery['name'],
            templateid=self.template_id)
        for item in items:
            item.update({'rule_id': rule_id, 'app_id': app_id})
            self._apply_item_prototype(item)

    def _apply_graph(self, graph):
        ZabbixGraph(self.zapi, graph, self.config, self.template_id).apply()

    def _apply_graphs(self):
        for graph in self.template.get('graphs', []):
            self._apply_graph(graph)

    def _apply_graph_prototype(self, prototype):
        ZabbixGraphPrototype(self.zapi, prototype, self.config, self.template_id).apply()

    def _apply_graph_prototypes(self, discovery):
        graphs = discovery.get('graphs', [])
        for graph in graphs:
            self._apply_graph_prototype(graph)

    def _apply_trigger(self, trigger):
        ZabbixTrigger(self.zapi, trigger, self.config, self.template_id).apply()

    def _apply_triggers(self):
        for trigger in self.template.get('triggers', []):
            self._apply_trigger(trigger)

    def _apply_trigger_prototype(self, prototype):
        ZabbixTriggerPrototype(self.zapi, prototype, self.config, self.template_id).apply()

    def _apply_trigger_prototypes(self, discovery):
        triggers = discovery.get('triggers', [])
        for triggers in triggers:
            self._apply_trigger_prototype(triggers)

    def _apply_autoreg(self):
        autoreg = self.template.get('autoreg')
        if autoreg:
            ZabbixAutoreg(self.zapi, self.template).apply()

    def _apply_trigger_action(self):
        alert = self.template.get('alert')
        if alert:
            ZabbixTriggerAction(self.zapi, self.template, self.config, self.template_id).apply()

    def _apply_discovery(self, discovery):
        ZabbixDiscovery(self.zapi, discovery, self.config, self.template_id).apply()

    def _apply_discoveries(self):
        discoveries = self.template.get('discovery', {})

        for app, discovery in discoveries.iteritems():
            app_id = self._apply_app(app)
            self._apply_discovery(discovery)
            self._apply_item_prototypes(discovery, app_id)
            self._apply_graph_prototypes(discovery)
            self._apply_trigger_prototypes(discovery)

    def _disable_item(self, id_):
        ZabbixItem(self.zapi).disable(id_)

    def _disable_app(self, app):
        items = self.zapi.get_id(
            'item',
            None,
            hostid=self.template_id,
            app_name=app)
        for item in items:
            self._disable_item(item)

    def clean(self):
        """
        Find and clean unused zabbix objects in current template.
        """

        def getUnusedObjects(type_, o):
            """
            Return list of unused zabbix objects of specific type in current template
            """

            unused_items = []
            # Get current objects from current template
            current_items = self.zapi.get_id(type_, templateids=self.template_id, name=True)
            if current_items:
                log.debug("Current %s: %s", type_, current_items)
                template_items = []
                for item in o:
                    if isinstance(item, dict):
                        template_items.append(item.get('name'))
                    else:
                        template_items.append(item)
                log.debug("Template %s: %s", type_, template_items)
                # Filter out similar objects from zabbix and template
                unused_items = filter(lambda x: x not in template_items, current_items)
                log.debug("Unused %s: %s", type_, unused_items)
            return { type_: unused_items }

        def removeObjects(template_objects):
            """
            Remove unused zabbix objects in current template.
            """

            # Find unused objects
            for objects in template_objects:
                unused_objects = getUnusedObjects(*objects)
                # Process each object type
                for type_, objects_list in unused_objects.iteritems():
                    # Get zabbix id for each unused object
                    for name in objects_list:
                        object_id = self.zapi.get_id(type_, name)
                        if object_id:
                            # Make function to remove object
                            func = 'self.zapi.{object_type}.delete'.format(object_type=type_)
                            log.info('Unused: %s \'%s\' was removed', type_, name)
                            eval(func)(object_id)

        # Init lists for objects
        items = apps = discovery = itemprototype = graphprototype = triggerprototype = []

        for app, item in self.template.get('applications', {}).iteritems():
            apps.append(app)
            items.extend(item)
        for app, disc in self.template.get('discovery', {}).iteritems():
            apps.append(app)
            discovery.append(disc)
            itemprototype.extend(disc.get('items', {}))
            graphprototype.extend(disc.get('graphs',{}))
            triggerprototype.extend(disc.get('triggers', {}))

        # Cleanup should be executed in folowing order
        obj_for_cleanup = collections.OrderedDict()
        obj_for_cleanup['application'] = apps
        obj_for_cleanup['item'] = items
        obj_for_cleanup['usermacro'] = map(lambda x: {'name':x.get('macro')}, self.template.get('macros', []))
        obj_for_cleanup['graph'] = self.template.get('graphs', [])
        obj_for_cleanup['trigger'] = self.template.get('triggers', [])
        obj_for_cleanup['discoveryrule'] = discovery
        obj_for_cleanup['itemprototype'] = itemprototype
        obj_for_cleanup['graphprototype'] = graphprototype
        obj_for_cleanup['triggerprototype'] = triggerprototype

        # Make tuple (obj_type, value) to compare with
        template_objects = []
        for k,v in obj_for_cleanup.iteritems():
            template_objects.append((k,v))

        # Remove unused objects
        removeObjects(template_objects)

    def apply(self):
        """
        Apply current template to zabbix.
        """

        self._apply_linked_templates()
        self.template_id = self._apply_template(self.template)

        # Cleanup unused objects
        self.clean()

        apps = self.template.get('applications', {})
        for app, items in apps.iteritems():
            # check if disabled whole app
            if str(items).lower() == 'disabled':
                self._disable_app(app)
            else:
                app_id = self._apply_app(app)
                self._apply_items(items, app_id)

        self._apply_macros()
        self._apply_graphs()
        self._apply_triggers()
        self._apply_discoveries()
        self._apply_autoreg()
        self._apply_trigger_action()
        log.info("Done: '%s'", self.template.get('name'))
