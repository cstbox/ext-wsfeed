# -*- coding: utf-8 -*-

import json

from pycstbox import log

_log = log.getLogger("wsfeed")


class VariableDefinition(object):
    _FIELDS = 'var_type unit threshold ttl'.split()
    _MANDATORY = ['var_type']

    _ALL_FIELDS = _FIELDS + ['last_updated', 'last_value']

    last_updated = None
    last_value = None

    def __init__(self, var_type, unit=None, threshold=0, ttl=3600*2):
        self.var_type = var_type
        self.unit = unit
        self.threshold = threshold
        self.ttl = ttl

    def __str__(self):
        return ', '.join(("%s=%s" % (attr, value) for attr, value in
                          ((attr, getattr(self, attr)) for attr in self._ALL_FIELDS)
                          if value)
                         )

    def as_dict(self):
        """ Returns the definition as a dictionary, omitting optional attributes which have no value
        :return:
        """
        return {
            k: self.__dict__[k] for k in self._FIELDS
            if k in self._MANDATORY or self.__dict__[k]
        }


class Configuration(object):
    DEFAULT_PATH = '/etc/cstbox/wsfeed.cfg'

    def __init__(self, path=DEFAULT_PATH):
        self._path = path or self.DEFAULT_PATH

        self._var_defs = {}
        self._gen_parms = {}

    @property
    def variable_definitions(self):
        return self._var_defs

    @property
    def general_parameters(self):
        return self._gen_parms

    def load(self):
        """ Loads the configuration from `path`, and returns it as two separate dictionaries,
        one containing the definitions of the variables, and the other containing the rest of
        the configuration.

        :return: the configuration data as two dictionaries
        :rtype: tuple(dict, dict)
        """
        cfg = json.load(file(self._path, 'rt'))
        var_defs = {n: VariableDefinition(**d) for n, d in cfg['variables'].iteritems()}
        del cfg['variables']

        self._var_defs = var_defs
        self._gen_parms = cfg

        return cfg, var_defs

    def save(self):
        data = {
            'variables': {n: d.as_dict() for n, d in self._var_defs.iteritems()},
        }
        data.update(self._gen_parms)

        _log.info('writing new configuration:')
        _log.info(data)

        json.dump(data, file(self._path, 'wt'), indent=4)
