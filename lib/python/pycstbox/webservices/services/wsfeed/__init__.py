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
    cfg, var_defs = load_configuration(path=settings.get('config_path', '/etc/cstbox/wsfeed.cfg'))
    update_handlers_initparms(cfg, var_defs)


def update_handlers_initparms(cfg, var_defs):
    _handlers_initparms['variables'] = var_defs
    _handlers_initparms.update(cfg)

_handlers_initparms = {}

handlers = [
    (r"/pushval", PushValues, _handlers_initparms),
    (r"/vardefs", VarDefAccess, _handlers_initparms),
]
