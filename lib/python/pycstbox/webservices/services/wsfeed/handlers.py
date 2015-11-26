# -*- coding: utf-8 -*-

import datetime
import json
import time

import dateutil

import pycstbox.evtmgr
from pycstbox import sysutils
from pycstbox.events import make_data
from pycstbox.webservices.wsapp import WSHandler

from pycstbox import wsfeed

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'


class BaseHandler(WSHandler):
    """ Root class for requests handlers.

    It takes care of storing shared resources retrieved when initializing the service module.

    It handles the optional request parameter `debug` which can be set to `1` for debugging
    features activation. The flag is reflected by the `_debug` private attribute of instances.

    The configuration passed as config parameter is a dictionary containing the following keys:
    - variables:
        A sub-dictionary providing the definition of managed variables. Each definition is a
        VariableDefinition namedtuple. The 'variables' sub-dictionary is keyed by the variable names
    - config:
        General configuration parameters
    """
    _config = None
    _debug = False
    _evtmgr = None
    _vars = None

    def initialize(self, logger=None, config=None, variables=None, **kwargs):
        super(BaseHandler, self).initialize(logger, **kwargs)

        # update class level dictionaries
        if not BaseHandler._vars:
            BaseHandler._vars = variables
        if not BaseHandler._config:
            BaseHandler._config = config

        self._evtmgr = self.get_event_manager()

    @staticmethod
    def get_event_manager():
        return pycstbox.evtmgr.get_object(pycstbox.evtmgr.SENSOR_EVENT_CHANNEL)

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
                nvt_parts = nvt.split(':', 2)
            except ValueError:
                self.error_reply('invalid nvt value', addit_infos=nvt, status_code=400)
                return

            else:
                name, arg_value = nvt_parts[:2]
                try:
                    arg_timestamp = nvt_parts[2]
                except IndexError:
                    arg_timestamp = None

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
                    var_meta = self._vars[name]

                    # check if we need to emit an event, depending on the variable nature, threshold and TTL
                    last_updated = var_meta.last_updated
                    if last_updated:
                        if self._debug:
                            self._logger.debug('last_updated=%s', datetime.datetime.fromtimestamp(last_updated / 1000.))

                        last_value = var_meta.last_value
                        if isinstance(value, bool):
                            emit = value != last_value
                        else:
                            elapsed = timestamp - last_updated
                            emit = \
                                abs(value - last_value) >= var_meta.threshold \
                                or elapsed >= var_meta.ttl * 1000
                        if self._debug:
                            self._logger.debug('last_value=%s value=%s elapsed=%d ttl=%d => emit=%s',
                                               last_value, value, elapsed, var_meta.ttl, emit
                                               )

                    else:
                        # never seen it before => emit
                        if self._debug:
                            self._logger.debug('first time seen: %s => emit', name)
                        emit = True

                    if emit:
                        events.append((timestamp, var_meta.var_type, name, json.dumps(make_data(value, var_meta.unit))))

                        var_meta.last_updated = timestamp
                        var_meta.last_value = value

                        # self._logger.info("_vars")
                        # for k, v in self._vars.iteritems():
                        #     self._logger.info("- %s=%s", k, v)

                except KeyError:
                    self.error_reply('undefined variable', addit_infos=name, status_code=404)
                    return

        for timestamp, var_type, name, data in events:
            self._evtmgr.emitFullEvent(timestamp, var_type, name, data)

        self.write({
            'event_count': len(events)
        })


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
        defs_dict = json.loads(self.request.body)
        try:
            var_defs = {n: wsfeed.VariableDefinition(**d) for n, d in defs_dict.iteritems()}

        except ValueError:
            self.error_reply('invalid JSON data', status_code=400)
            return

        else:
            # load the current configuration
            cfg = wsfeed.Configuration()
            cfg.load()

            # replace the variables dictionary by the new definitions
            cfg.variable_definitions.clear()
            cfg.variable_definitions.update(var_defs)
            # TODO definitions checking

            # save the updated configuration
            cfg.save()

            # reload the definitions
            gen_parms, var_defs = cfg.load()
            from ..wsfeed import update_handlers_initparms
            update_handlers_initparms(gen_parms, var_defs)


