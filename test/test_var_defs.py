#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import unittest
import requests
import json


VAR_DEFS = {
    "current": {
        "var_type": "current",
        "unit": "A"
    },
    "door_opened": {
        "var_type": "opened"
    },
    "temp": {
        "var_type": "temperature",
        "unit": "degC"
    }
}


class VarDefsTestCase(unittest.TestCase):
    def _get_vardefs(self):
        response = requests.get("http://localhost:8888/api/wsfeed/vardefs")
        self.assertTrue(response.ok)
        return json.loads(response.content)

    def test_get_defs(self):
        vardefs = self._get_vardefs()
        self.assertNotEqual(len(vardefs.keys()), 0)

    def test_set_defs(self):
        new_defs = {
            'foo': {
                "var_type": "voltage",
                "unit": "V"
            }
        }
        new_defs.update(VAR_DEFS)
        response = requests.post("http://localhost:8888/api/wsfeed/vardefs", data=json.dumps(new_defs))
        self.assertTrue(response.ok)

        vardefs = self._get_vardefs()
        self.assertTrue('foo' in vardefs)

        # back to default values
        response = requests.post("http://localhost:8888/api/wsfeed/vardefs", data=json.dumps(VAR_DEFS))
        self.assertTrue(response.ok)
        vardefs = self._get_vardefs()
        self.assertFalse('foo' in vardefs)


if __name__ == '__main__':
    unittest.main()
