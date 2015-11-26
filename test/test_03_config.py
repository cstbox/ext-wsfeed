#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os

from pycstbox import wsfeed

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'


class WSFeedConfigTestCase(unittest.TestCase):
    CFG_PATH = '/tmp/wsfeed.cfg'

    @classmethod
    def setUpClass(cls):
        cls.config = wsfeed.Configuration(cls.CFG_PATH)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.CFG_PATH)
        except OSError:
            pass

    def _dump_cfg_file(self):
        print
        for line in file(self.CFG_PATH):
            print(line.rstrip())

    def test_01(self):
        self.config.save()
        self.assertTrue(os.path.isfile(self.CFG_PATH))

    def test_02(self):
        self.config.variable_definitions['x'] = wsfeed.VariableDefinition('temperature', 'degC')
        self.config.save()
        # self._dump_cfg_file()

        cfg_check = wsfeed.Configuration(self.CFG_PATH)
        cfg_check.load()
        self.assertTrue('x' in cfg_check.variable_definitions)
        vd = cfg_check.variable_definitions['x']
        self.assertEqual(vd.var_type, 'temperature')
        self.assertEqual(vd.unit, 'degC')
        self.assertEqual(vd.threshold, 0)
        self.assertEqual(vd.ttl, 7200)

        self.assertFalse('variables' in cfg_check.general_parameters)

    def test_03(self):
        self.config.variable_definitions['x'] = wsfeed.VariableDefinition('temperature', 'degC')
        self.config.general_parameters['foo'] = 'baz'
        self.config.general_parameters['bar'] = 42
        self.config.save()
        # self._dump_cfg_file()

        cfg_check = wsfeed.Configuration(self.CFG_PATH)
        cfg_check.load()
        self.assertTrue('x' in cfg_check.variable_definitions)
        self.assertEqual(cfg_check.general_parameters['foo'], 'baz')
        self.assertEqual(cfg_check.general_parameters['bar'], 42)

if __name__ == '__main__':
    unittest.main()
