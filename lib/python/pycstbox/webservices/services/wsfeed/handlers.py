#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import time
from collections import namedtuple

from pycstbox.webservices.wsapp import WSHandler
import pycstbox.evtmgr
from pycstbox.events import make_timed_event


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

        if not variables:
            raise ValueError('empty variables definition list provided')

        self._vars = variables
        self._evtmgr = pycstbox.evtmgr.get_object(pycstbox.evtmgr.SENSOR_EVENT_CHANNEL)

    def prepare(self):
        self._debug = bool(self.get_argument('debug', 0))


class PushValues(BaseHandler):
    """ Posts one or several variable values.

    The corresponding sensor events are built and broadcast on the sensor event bus.

    Request arguments:
        var
            (mandatory) one or more (name, value) pairs, containing the name and the value
            of each pushed variable. Items are joined by a colon char (':')
    """
    def do_post(self, var_name):
        var_list = self.get_arguments('var')

        # use the same timestamp for all posted events since they are submitted at the same time
        timestamp = int(time.time() * 1000)

        for nv in var_list:
            name, value = nv.split(':')
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    v = value.lower()
                    if v in ('true', 't', 'yes', 'y', '1'):
                        value = True
                    elif v in ('false', 'f', 'no', 'n', '0'):
                        value = False
                    else:
                        raise ValueError('invalid value (%s) for variable (%s)' % (value, name))

            try:
                var_def = self._vars[name]
                event = make_timed_event(timestamp, var_def.var_type, name, value, var_def.unit)
                self._evtmgr.emitTimedEvent(event)
            except KeyError:
                raise ValueError('undefined variable (%s)' % name)


VariableDefinition = namedtuple('VariableDefinition', 'var_type', 'unit')