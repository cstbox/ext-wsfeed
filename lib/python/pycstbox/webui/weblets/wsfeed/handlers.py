# -*- coding: utf-8 -*-

""" WSFeed configuration weblet """

import logging

from pycstbox import webui

from pycstbox import wsfeed

__author__ = 'Eric PASCUAL - CSTB (eric.pascual@cstb.fr)'

# allows catching Exception instances
#pylint: disable=W0703

_logger = logging.getLogger('wblt-wsfeed')


class GetVarDefsHandler(webui.WSHandler):
    def do_get(self):
        try:
            cfg = wsfeed.Configuration()
            cfg, var_defs = cfg.load()
        except Exception as e:
            _logger.exception(e)
            raise
        else:
            self.finish({n: d.as_dict() for n, d in var_defs.iteritems()})


class DisplayHandler(webui.WebletUIRequestHandler):
    """ UI display request handler """
    def get(self):
        config = wsfeed.Configuration()
        config.load()

        self.render(
            "wsfeed.html",
            var_defs=config.variable_definitions,
            gen_parms=config.general_parameters
        )
        if self.application.settings['debug']:
            _logger.setLevel(logging.DEBUG)


handlers = [
    ("/vardefs", GetVarDefsHandler),

    (r"[/]?", DisplayHandler)
]


