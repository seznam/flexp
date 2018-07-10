from __future__ import absolute_import

import os
import pickle
import shutil
import unittest
from flexp.flow import cache
from .utils import Add, Mult


class TestCache(unittest.TestCase):
    """Test the content of cache."""

    cache_dir = "tests/cached_pkls"

    def setUp(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def _load_cache_file(self, pickle_cache, data):
        """Read first value from cache dir."""
        file = pickle_cache.get_cache_file(data)
        return pickle.load(open(file, 'rb'))

    def test_cache(self):
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Add(13),
        ])
        c.process({"input": 10})
        c.close()

        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 23})

        # Run it again to use cached file
        c.process({"input": 10})
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 23})

    def test_pickle_cache_attr_change(self):
        """PickleCache should change the saved value if modules' attributes differ."""
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Add(13),
        ])
        c.process({"input": 10})
        c.close()
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 23})

        # Change the add attribute
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Add(10),
        ])
        c.process({"input": 10})
        c.close()
        # The cache content must change because the modules parameters are different
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 20})

    def test_pickle_cache_module_replace(self):
        """PickleCache should change the saved value if modules differ."""
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Add(13),
        ])
        c.process({"input": 10})
        c.close()

        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 23})

        # Change the module, keep attributes
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Add(100),
        ])
        c.process({"input": 10})
        c.close()
        # The cache content must change because the modules parameters are different
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 110})

        # Change the module, keep attributes
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Mult(13),
        ])
        c.process({"input": 10})
        c.close()
        # The cache content must change because the modules parameters are different
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 130})

        # Change the module, keep attributes
        c = cache.PickleCache(self.cache_dir, "input", chain=[
            Mult(130),
        ])
        c.process({"input": 10})
        c.close()
        # The cache content must change because the modules parameters are different
        self.assertEqual(self._load_cache_file(c, {"input": 10})["data"],
                         {"input": 10, "output": 1300})
