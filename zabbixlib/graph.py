import logging
from object import ZabbixObject

log = logging.getLogger(__name__)


class ZabbixGraph(ZabbixObject):

    """
    Implements working with zabbix graph objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix graph template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        self.obj_type = 'graph'
        self.zbx_item_class = 'item'
        ZabbixObject(self.zapi, self.obj, self.template_id)

    def _get_y_value(self, type_, value):
        result = None
        if type_ == self.defaults['y_min_max_type'].index('fixed'):
            result = float(value)
        elif type_ == self.defaults['y_min_max_type'].index('item'):
            result = self.zapi.get_id(
                self.zbx_item_class,
                value,
                hostid=self.template_id)
        logging.debug(
            '_get_y_valye({0},{1}): {2}'.format(
                type_,
                value,
                result))
        return result

    def _create_graph_items_req(self, req):
        """
        Create request for graph items changes.

        Return  (str)   Request for changes.
        """

        gitems = self.obj.get('items', [])
        req['gitems'] = []

        for gitem in gitems:
            item_id = self.zapi.get_id(
                self.zbx_item_class,
                gitem['item'],
                hostid=self.template_id)

            item = {
                'itemid': item_id,
                'color': gitem.get(
                    'color',
                    self.defaults['default']['graph']['color']),
                'sorted': gitems.index(gitem),
                'calc_fnc': self.defaults['graph_func'].get(
                    gitem.get(
                        'func',
                        self.defaults['default']['graph']['func']).lower()),
                'yaxisside': {
                    'left': 0,
                    'right': 1}.get(
                        gitem.get(
                            'y_side',
                            self.defaults['default']['graph']['y_side']).lower()),
            }

            type_ = self.obj.get(
                'type',
                self.defaults['default']['graph']['type']).lower()

            item.update(
                {
                    'normal': {
                        'drawtype': self.defaults['graph_style'].index(
                            gitem.get(
                                'style', self.defaults['default']['graph']['style']).lower())}, 'pie': {
                        'type': {
                            'simple': 0, 'graph sum': 2}.get(
                                gitem.get(
                                    'type', self.defaults['default']['graph']['gitype']).lower())}}.get(
                                        type_, {}))

            req['gitems'].append(item)

    def _create_request(self):
        """
        Create request for changes.

        Return  (str)   Request for changes.
        """

        result = {
            'name': self.obj['name'],
            'width': int(
                self.obj.get(
                    'width',
                    self.defaults['default']['graph']['width'])),
            'height': int(
                self.obj.get(
                    'height',
                    self.defaults['default']['graph']['height'])),
            'graphtype': self.defaults['graph_type'].index(
                self.obj.get(
                    'type',
                    self.defaults['default']['graph']['type']).lower()),
        }

        type_ = self.obj.get(
            'type',
            self.defaults['default']['graph']['type']).lower()

        {
            'normal': self._normal_graph_req,
            'stacked': self._stacked_graph_req,
            'pie': self._pie_graph_req,
            'exploded': self._exploded_graph_req,
        }[type_](result)

        return result

    def _stacked_graph_req(self, req):
        """
        Create request for Stacked graph changes.

        Return  (str)   Request for changes.
        """

        self._create_graph_items_req(req)

        req.update(
            {
                'show_legend': int(
                    bool(
                        self.obj.get(
                            'show_legend',
                            self.defaults['default']['graph']['show_legend']))),
                'show_work_period': int(
                    bool(
                        self.obj.get(
                            'show_working_time',
                            self.defaults['default']['graph']['show_working_time']))),
                'show_triggers': int(
                    bool(
                        self.obj.get(
                            'show_triggers',
                            self.defaults['default']['graph']['show_triggers']))),
                'ymin_type': self.defaults['graph_y_type'].index(
                    self.obj.get(
                        'y_min_type',
                        self.defaults['default']['graph']['y_min_type']).lower()),
                'ymax_type': self.defaults['graph_y_type'].index(
                    self.obj.get(
                        'y_max_type',
                        self.defaults['default']['graph']['y_max_type']).lower()),
            })

        if req['ymin_type'] == self.defaults['y_min_max_type'].index('fixed'):
            req.update(
                {'yaxismin': self._get_y_value(req['ymin_type'], self.obj.get('y_min')), })
        elif req['ymin_type'] == self.defaults['y_min_max_type'].index('item'):
            req.update(
                {'ymin_itemid': self._get_y_value(req['ymin_type'], self.obj.get('y_min')), })

        if req['ymax_type'] == self.defaults['y_min_max_type'].index('fixed'):
            req.update(
                {'yaxismax': self._get_y_value(req['ymax_type'], self.obj.get('y_max')), })
        elif req['ymax_type'] == self.defaults['y_min_max_type'].index('item'):
            req.update(
                {'ymax_itemid': self._get_y_value(req['ymax_type'], self.obj.get('y_max')), })

        log.debug('Stacked graph:')

    def _normal_graph_req(self, req):
        """
        Create request for Normal graph changes.

        Return  (str)   Request for changes.
        """

        self._stacked_graph_req(req)

        req.update({'percent_right': self.obj.get('percent_right',
                                                  self.defaults['default']['graph']['percent_right']),
                    'percent_left': self.obj.get('percent_left',
                                                 self.defaults['default']['graph']['percent_left']),
                    })
        log.debug('Normal graph:')

    def _pie_graph_req(self, req):
        """
        Create request for Pie graph changes.

        Return  (str)   Request for changes.
        """

        self._create_graph_items_req(req)

        req.update(
            {
                'show_legend': int(
                    bool(
                        self.obj.get(
                            'show_legend',
                            self.defaults['default']['graph']['show_legend']))),
                'show_3d': int(
                    bool(
                        self.obj.get(
                            '3d_view',
                            self.defaults['default']['graph']['show_legend'])))})
        log.debug('Pie graph:')

    def _exploded_graph_req(self, req):
        """
        Create request for Exploded graph changes.

        Return  (str)   Request for changes.
        """

        self._pie_graph_req(req)
        log.debug('Exploded graph:')

    def apply(self):
        """
        Push graph object to zabbix server.
        """

        result = None
        req = self._create_request()

        log.info("%s: '%s'", str(self.obj_type).capitalize(), self.obj['name'])

        # Get 'graph' or 'graphprototype' object id
        obj_id = self.zapi.get_id(
            self.obj_type,
            self.obj['name'],
            hostid=self.template_id)

        if obj_id:
            req.update({'graphid': obj_id})
            zbx_method = 'update'
        else:
            zbx_method = 'create'

        func = "self.zapi.{obj_type}.{zbx_method}".format(
            obj_type=self.obj_type,
            zbx_method=zbx_method)
        log.debug('%s: %s', func, req)
        result = eval(func)(req)

        return result


class ZabbixGraphPrototype(ZabbixGraph):

    """
    Implements working with zabbix graph prototype objects.

    Arguments:
    zapi        (ZabbixAPI)       ZabbixAPI connector to send request.
    obj         (dict)            Dictionary discribed zabbix graph prototype template.
    defaults    (ZabbixDefaults)  Default values.
    template_id (int)             Zabbix Template id.
    """

    def __init__(self, zapi, obj, defaults, template_id):
        self.zapi = zapi
        self.obj = obj
        self.defaults = defaults
        self.template_id = template_id
        ZabbixGraph(self.zapi, self.obj, self.defaults, self.template_id)

    def _create_request(self):
        """
        Create request for graph prototype changes.

        Return  (str)   Request for changes.
        """

        self.obj_type = 'graphprototype'
        self.zbx_item_class = 'itemprototype'
        return super(ZabbixGraphPrototype, self)._create_request()
