#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Web services API for external data feed.
"""

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

from pycstbox import log
from .handlers import *


def _init_(logger=None, settings=None):
    """ Module init function, called by the application framework during the
    services discovery process.

    settings expected content:
        - config_path :
            service configuration file path, containing the definitions of
            the pushed variables
    """

    # inject the (provided or created) logger in handlers default initialize parameters
    _handlers_initparms['logger'] = logger if logger else log.getLogger('svc.wsfeed')

    # same for services configuration
    import json
    try:
        cfg_path = settings.get('config_path', '/etc/cstbox/wsfeed.cfg')
        cfg = json.load(file(cfg_path, 'rt'))
        var_defs = {}
        for name, definition in cfg['variables'].iteritems():
            var_defs[name] = VariableDefinition(definition['var_type'], definition.get('unit', None))

        _handlers_initparms['variables'] = var_defs
        del cfg['variables']
        _handlers_initparms.update(cfg)

    finally:
        del json


_handlers_initparms = {}

handlers = [
    (r"/pushval", PushValues, _handlers_initparms),
]
