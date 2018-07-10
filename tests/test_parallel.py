from __future__ import print_function

import time
import unittest

from flexp.flow.parallel import parallelize


def add_two(x):
    return x + 2


class TestParallel(unittest.TestCase):

    def test_parallel(self):
        count = 50
        data = range(0, count)

        start = time.clock()
        res = list(parallelize(add_two, data, 25))
        end = time.clock()
        print("Time to process {}".format(end - start))
        assert len(res) == count
        assert sum(res) == (2 + count + 1) * count / 2
