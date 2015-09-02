#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import time
from collections import namedtuple
import json
import dateutil

from pycstbox.webservices.wsapp import WSHandler
import pycstbox.evtmgr
from pycstbox.events import make_data
from pycstbox import sysutils


class BaseHandler(WSHandler):
    """ Root class for requests handlers.

    It takes care of storing shared resources retrieved when initializing the service module.

    It handles the optional request parameter `debug` which can be set to `1` for debugging
    features activation. The flag is reflected by the `_debug` private attribute of instances.

    The configuration passed as config parameter is a dictionary containing the following keys:
    - variables:
        A sub-dictionary providing the definition of managed variables. Each definition is a
        VariableDefinition namedtuple. The 'variables' sub-dictionary is keyed by the variable names
    - ...:
        other configuration keys as stored in the configuration file
    """
    _config = None
    _debug = False
    _evtmgr = None
    _vars = None

    def initialize(self, logger=None, variables=None, **kwargs):
        super(BaseHandler, self).initialize(logger, **kwargs)

        self._vars = variables
        self._evtmgr = pycstbox.evtmgr.get_object(pycstbox.evtmgr.SENSOR_EVENT_CHANNEL)

    def prepare(self):
        self._debug = bool(self.get_argument('debug', 0))


class PushValues(BaseHandler):
    """ Posts one or several variable values.

    The corresponding sensor events are built and broadcast on the sensor event bus.
    """
    def do_post(self):
        """ Post events according the provided variable values.

        Request arguments:
            - nvt
                (mandatory) one or more (name, value[, timestamp]) tuples, containing the name and the value
                of each pushed variable. A specific time stamp can be provided as the optional third item.
                Tuple items are joined by a colon char (':'). Time stamp is provided either as the decimal
                seconds count since Epoch or as a valid ISO8601 string.
        """
        if not self._vars:
            msg = 'no variable definition available'
            self._logger.error(msg)
            self.error_reply(msg)
            return

        nvt_list = self.get_arguments('nvt')

        # default time stamp is the same for all posted events since they are submitted at the same time
        dflt_timestamp = int(time.time() * 1000)

        events = []

        for nvt in nvt_list:
            try:
                name, arg_value, arg_timestamp = (nvt.split(':', 2) + (None,))[:3]
            except ValueError:
                self.error_reply('invalid nvt value', addit_infos=nvt, status_code=400)
                return

            else:
                # try to interpret the value field
                try:
                    value = int(arg_value)
                except ValueError:
                    try:
                        value = float(arg_value)
                    except ValueError:
                        v = arg_value.lower()
                        if v in ('true', 't', 'yes', 'y', '1'):
                            value = True
                        elif v in ('false', 'f', 'no', 'n', '0'):
                            value = False
                        else:
                            self.error_reply('invalid value',
                                             addit_infos={'name': name, 'value': arg_value},
                                             status_code=400)
                            return

                # process the time stamp if provided
                if arg_timestamp:
                    # is it a second count ?
                    try:
                        timestamp = int(float(arg_timestamp) * 1000)
                    except ValueError:
                        # maybe an ISO time stamp ?
                        try:
                            dt = dateutil.parser.parse(arg_timestamp)
                            timestamp = sysutils.to_milliseconds(dt)
                        except:
                            self.error_reply('invalid time stamp',
                                             addit_infos={'name': name, 'timestamp': arg_timestamp},
                                             status_code=400)
                            return
                else:
                    timestamp = dflt_timestamp

                try:
                    var_def = self._vars[name]
                    events.append((timestamp, var_def.var_type, name, json.dumps(make_data(value, var_def.unit))))
                except KeyError:
                    self.error_reply('undefined variable', addit_infos=name, status_code=404)
                    return

        for timestamp, var_type, name, data in events:
            self._evtmgr.emitFullEvent(timestamp, var_type, name, data)


class VarDefAccess(BaseHandler):
    def do_get(self):
        """ Returns the current variable definitions as a JSON document
        """
        result = {v_name: v_def.as_dict() for v_name, v_def in self._vars.iteritems()}
        self.write(result)

    def do_post(self):
        """ Updates the definitions of variables.

        Data are provided in JSON format as the request body
        """
        try:
            defs = json.loads(self.request.body)

        except ValueError:
            self.error_reply('invalid JSON data', status_code=400)
            return

        else:
            cfg = json.load(file(_config_path, 'rt'))
            cfg['variables'] = defs
            # TODO definitions checking
            json.dump(cfg, file(_config_path, 'wt'), indent=4)
            cfg, var_defs = load_configuration(_config_path)

            # reload definitions
            from ..wsfeed import update_handlers_initparms
            update_handlers_initparms(cfg, var_defs)


class VariableDefinition(namedtuple('VariableDefinition', 'var_type unit')):
    __slots__ = ()

    def as_dict(self):
        d = {k: self.__dict__[k] for k in ('var_type', 'unit')}
        if not self.unit:
            del d['unit']
        return d


_config_path = None


def load_configuration(path):
    global _config_path
    if not _config_path:
        _config_path = path

    cfg = json.load(file(_config_path, 'rt'))
    var_defs = {}
    for name, definition in cfg['variables'].iteritems():
        var_defs[name] = VariableDefinition(definition['var_type'], definition.get('unit', None))
    del cfg['variables']

    return cfg, var_defs
