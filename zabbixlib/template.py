import fnmatch
import logging
import os
import pprint
import yaml
from group import ZabbixGroups

log = logging.getLogger(__name__)


class ZabbixTemplate(object):

    """
    Implements working with zabbix template objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix template.
    """

    def __init__(self, zapi, obj):
        self.zapi = zapi
        self.obj = obj
        self.obj_type = 'template'

    def _create_request(self):
        """
        Create request for template changes.

        Return  (str)   Request for changes.
        """

        return {'groups': ZabbixGroups(self.zapi, self.obj['groups']).apply()}

    def apply(self):
        """
        Push template object to zabbix server.
        """

        result = None
        req = self._create_request()
        log.info("%s: '%s'", str(self.obj_type).capitalize(), self.obj['name'])

        # Get linked templates id
        if self.obj.get('templates'):
            req['templates'] = self.zapi.get_id(
                'template',
                self.obj['templates'])

        # Get current template id
        self.template_id = self.zapi.get_id('template', self.obj['name'])

        if self.template_id:
            req['templateid'] = self.template_id
            result = self.zapi.template.update(req)
        else:
            req['host'] = self.obj['name']
            result = self.zapi.template.create(req)

        result = result['templateids'][0]
        return result


class ZabbixTemplateFile(dict):

    """
    Load and Save locally resulting zabbix template.

    Attributes:
      name (str):           Name of template for load
      pattern (str):        Pattern to search for templates. Default: '*'
      basedir (str):        Directory that store zabbix templates.
                            Default: './templates'
      file_extension (str): Extension for template files. Default: '.yaml'
    """

    def __init__(
            self,
            name,
            pattern='*',
            basedir='./',
            file_extension='.yaml',
            templates_dir=None):
        self.name = name
        self.file_extension = file_extension
        self.pattern = pattern + self.file_extension
        self.basedir = '{0}/{1}'.format(basedir, name)
        self.templates_dir = templates_dir
        # Load template from files
        self.template = {}
        self.processed_items = 0
        self.template = self._load(self.basedir)

    def _walk(self, basedir):
        """
        Return list of files for current template
        """

        result = []

        for root, dirs, files in os.walk(basedir):
            for file_ in fnmatch.filter(files, self.pattern):
                result.append(os.path.join(root, file_))

        return result

    def _search(self):
        """
        Try to find template in template_dir
        """

        result = None

        # get list of files
        files_list = self._walk(self.templates_dir)

        for file_ in files_list:
            with open(file_, 'r') as f:
                line = f.readline()
                if line[0:5] == 'name:':
                    name = line[5:].strip(' \'\"\n')
                    if name == self.name:
                        result = os.path.dirname(file_)
                        log.debug('Found Template: "%s" in %s', name, result)
                        break
        return result

    def _merge(self, t1, t2):
        """
        Merge two templates.

        Attributes:
          t1 (dict)
          t2 (dict)
        """

        for k, v in t2.iteritems():
            if t1.get(k, {}) == {}:
                t1[k] = v
            else:
                if isinstance(t2.get(k, {}), dict):
                    t1.get(k, {}).update(v)
                elif isinstance(t2.get(k), list):
                    t1.get(k).extend(v)
                else:
                    t1[k] = v

        log.debug('Template result:\n%s', t1)

    def _load(self, basedir):
        """
        Load current template from files and save it class variable.
        """

        result = {}

        files_list = self._walk(basedir)
        log.debug("Template files list: %s", files_list)

        for file_ in files_list:
            # Read template file
            with open(file_) as f:
                str_buf = f.read()
                # Load template
                template = yaml.safe_load(str_buf)
                log.debug(
                    'Template loaded from "%s":\n%s',
                    file_,
                    template)
                # Merge template
                self._merge(result, template)

        if not result:
            log.debug("Trying find template in %s", self.templates_dir)
            template_dir = self._search()
            if template_dir:
                result = self._load(template_dir)
        else:
            # Save template in class variable
            log.debug('Combined template:\n%s', result)
            log.info("Template '%s' was fully loaded.", result['name'])

        return result

    def __getitem__(self, item, value=None):
        return self.template.get(item, value)

    def __setitem__(self, item, value):
        self.template[item] = value

    def __repr__(self):
        pf = pprint.PrettyPrinter(indent=4).pformat
        return pf(self.template)

    def iteritems(self):
        return iter(self.template.iteritems())

    def get(self, item, value=None):
        return self.__getitem__(item, value)

    def __bool__(self):
        return bool(self.template)

    __nonzero__ = __bool__
