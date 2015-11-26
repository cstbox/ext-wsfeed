#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Web services API for external data feed.
"""

from pycstbox import log
from pycstbox import wsfeed

from .handlers import *

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'


def _init_(logger=None, settings=None):
    """ Module init function, called by the application framework during the
    services discovery process.

    settings expected content:
        - config_path :
            service configuration file path, containing the definitions of
            the pushed variables
    """

    def log_config_dict(d, label):
        logger.info(label)
        if d:
            for k, v in d.iteritems():
                logger.info("- %s: %s", k, v)
        else:
            logger.info('* empty *')

    # inject the (provided or created) logger in handlers default initialize parameters
    logger = logger or log.getLogger('svc.wsfeed')
    _handlers_initparms['logger'] = logger

    # same for services configuration
    cfg = wsfeed.Configuration(path=settings.get('config_path', None))
    cfg, var_defs = cfg.load()

    log_config_dict(cfg, 'configuration:')
    log_config_dict(var_defs, 'definitions:')

    update_handlers_initparms(cfg, var_defs)


def update_handlers_initparms(cfg, var_defs):
    _handlers_initparms['variables'] = var_defs
    _handlers_initparms['config'] = cfg

_handlers_initparms = {}

handlers = [
    (r"/pushval", PushValues, _handlers_initparms),
    (r"/vardefs", VarDefAccess, _handlers_initparms),
]
