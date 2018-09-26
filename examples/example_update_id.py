from __future__ import absolute_import

from flexp.flow import cache, Chain
from flexp.flow.cache import PickleCache
from flexp.flow.caching_chain import CachingChain
from flexp import flexp

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
    flexp.setup("./experiments", "tf-idf", with_date=True)

    data = FlowData()

    my_chain = CachingChain([
        PrintIdModule(),
        PickleCache("cached_pkl", "id", [TestModule(12, 14, 18)]),
        PrintIdModule(),
        PickleCache("cached_pkl", "id", [TestModule(12, 16, 18)]),
        PrintIdModule(),
        TestModule(12, 16, 20),
        PrintIdModule(),
        PrintIdModule(),

    ], update_data_id='id')

    my_chain.process(data)

if __name__ == "__main__":
    main()
