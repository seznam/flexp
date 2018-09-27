from __future__ import absolute_import

import os
import pickle
import shutil
import unittest
from flexp.flow import cache


class TestModule:

    PickleCacheBlackList = ['attr3']

    def __init__(self, attr1, attr2, attr3):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3
        # self.cache_bckl = ['attr3']

    def process(self, data):
        pass


class TestCache(unittest.TestCase):
    """Test the hash of cache and black list parameter"""

    cache_dir = "tests/cached_pkls"

    def setUp(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def test_cache(self):

        c = cache.PickleCache(self.cache_dir, "input", chain=[
            TestModule(12, 14, 18),
        ])
        c.process({"input": 10})

        # different value for attribute from black list
        c2 = cache.PickleCache(self.cache_dir, "input", chain=[
            TestModule(12, 14, 20),
        ])
        c2.process({"input": 10})
        self.assertEqual(c.chain_info['chain_hash'], c2.chain_info['chain_hash'])

        # different value for attribute that is not in black list
        c3 = cache.PickleCache(self.cache_dir, "input", chain=[
            TestModule(12, 12, 18),
        ])
        c3.process({"input": 10})
        self.assertFalse(c.chain_info['chain_hash'] == c3.chain_info['chain_hash'])

        c.close()
        c2.close()
        c3.close()
