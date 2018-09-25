from __future__ import absolute_import

import os
import pickle
import shutil
import unittest
from flexp.flow import cache, Chain
from flexp.flow.cache import PickleCache
from flexp.flow.caching_chain import CachingChain
from tests.utils import Add


class PrintIdModule:

    def process(self, data):
        print(data.id)


class TestModule:

    PickleCacheBlackList = ['attr3']
    UpdateDataId = "id"

    def __init__(self, attr1, attr2, attr3):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3
        # self.cache_bckl = ['attr3']

    def process(self, data):
        pass


class FlowData():

    def __init__(self):
        self.id = "/adsasd/asdasd/asdad/asd"

    def __iter__(self):
        return iter(self.__dict__)

    def items(self):
        return [(attr, getattr(self, attr)) for attr in self.__dict__]

    def __setitem__(self, key, item):
        setattr(self, key, item)

    def __getitem__(self, key):
        return getattr(self, key)

# class TestUpdateId(unittest.TestCase):
#     """Test the hash of cache and black list parameter"""

def main():
    cache_dir = "tests/cached_pkls"

    # def setUp(self):
    #     if os.path.exists(self.cache_dir):
    #         shutil.rmtree(self.cache_dir)
    #
    # def tearDown(self):
    #     if os.path.exists(self.cache_dir):
    #         shutil.rmtree(self.cache_dir)
    #
    # def test_cache(self):
    print("start")
    my_chain_1 = cache.PickleCache(cache_dir, "input", chain=[
        TestModule(12, 14, 18),
    ])
    # my_chain_1.process({"input": 10})

    # different value for attribute from black list
    my_chain_2 = cache.PickleCache(cache_dir, "input", chain=[
        TestModule(12, 16, 20),
    ])
    # my_chain_2.process({"input": 10})
    # self.assertEqual(c.chain_info['chain_hash'], c2.chain_info['chain_hash'])

    # different value for attribute that is not in black list
    my_chain_3 = cache.PickleCache(cache_dir, "input", chain=[
        TestModule(12, 18, 18),
    ])
    # my_chain_3.process({"input": 10})
    # self.assertFalse(c.chain_info['chain_hash'] == c3.chain_info['chain_hash'])
    data = FlowData()

    my_chain = CachingChain([
        PrintIdModule(),
        PickleCache("cached_pkl", "id", my_chain_1),
        PrintIdModule(),
        PickleCache("cached_pkl", "id", my_chain_2),
        PrintIdModule(),
        TestModule(12, 16, 20),
        PrintIdModule(),
        PickleCache("cached_pkl", "id", my_chain_3),
        PrintIdModule(),
        PrintIdModule(),

    ], update_data_id='id')

    my_chain.process(data)

if __name__ == "__main__":
    main()
