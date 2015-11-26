#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import requests
import json

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'


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
        "unit": "degC",
        "threshold": 1
    }
}


class FeedTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requests.post("http://localhost:8888/api/wsfeed/vardefs", data=json.dumps(VAR_DEFS))

    def test_01(self):
        args = {
            'nvt': "temp:20:2015-11-20 21:00:00"
        }
        response = requests.post("http://localhost:8888/api/wsfeed/pushval", params=args)
        self.assertTrue(response.ok)

        resp = json.loads(response.content)
        self.assertEqual(resp['event_count'], 1)

        args = {
            'nvt': "temp:20:2015-11-20 21:10:00"
        }
        response = requests.post("http://localhost:8888/api/wsfeed/pushval", params=args)
        resp = json.loads(response.content)
        self.assertEqual(resp['event_count'], 0)

        args = {
            'nvt': "temp:21:2015-11-20 21:11:00"
        }
        response = requests.post("http://localhost:8888/api/wsfeed/pushval", params=args)
        resp = json.loads(response.content)
        self.assertEqual(resp['event_count'], 1)

        args = {
            'nvt': "temp:21:2015-11-20 21:30:00"
        }
        response = requests.post("http://localhost:8888/api/wsfeed/pushval", params=args)
        resp = json.loads(response.content)
        self.assertEqual(resp['event_count'], 0)

        args = {
            'nvt': "temp:21:2015-11-20 23:30:00"
        }
        response = requests.post("http://localhost:8888/api/wsfeed/pushval", params=args)
        resp = json.loads(response.content)
        self.assertEqual(resp['event_count'], 1)

if __name__ == '__main__':
    unittest.main()
