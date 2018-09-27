#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FILE         $Id$
AUTHOR       Ksenia Shakurova <ksenia.shakurova@firma.seznam.cz>

Copyright (c) 2017 Seznam.cz, a.s.
All rights reserved.
"""
import argparse

import common.flow.flog as flog
from common.flow import Chain
from flexp import flexp
from flexp.flow.cache import PickleCache

log = flog.Log(__name__)

from flexp.flow import cache


# define module with some attributes
class TestModule:
    # PickleCacheBlackList will be the list
    PickleCacheBlackList = ['attr3']

    def __init__(self, attr1, attr2, attr3):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3  # this parameter will be skipped

    def process(self, data):
        #....
        pass


class FlowData(object):

    def __init__(self):
        self.id = ""
        self.attrs = [1, 2, 3]

    def __iter__(self):
        return iter(self.__dict__)

    def items(self):
        return [(attr, getattr(self, attr)) for attr in self.__dict__]

    def __setitem__(self, key, item):
        setattr(self, key, item)

    def __getitem__(self, key):
        return getattr(self, key)


def main():
    flexp.setup("experiments/", "exp01", False)

    flog.setup("debug", path=flexp.get_file_path("experiment.log.txt"))  # , disable_stderr=not cfg.SHORT_RUN)
    log.debug('Starting.')

    data = FlowData()
    data.id = "a"

    # debug level 2 - all detailes will be printed
    data_chain = PickleCache("cached_pkls", "id", chain=[TestModule(12, 14, 18)], debug_level=2)
    data_chain.process(data)

    # hash of this and previous are same
    data_chain = PickleCache("cached_pkls", "id", chain=[TestModule(12, 14, 20)], debug_level=1)
    data_chain.process(data)


if __name__ == "__main__":
    main()
