"""Inspector has the ability to print out data flowing through any module.

Usage: Chain([inspect(MyModule())])
"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import collections
import pprint

from flexp.flow import Chain
from flexp.utils import get_logger


log = get_logger(__name__)


def inspect(module, stream=False, depth=3):
    """Inspect module's data flow based on its keys `requires` and `provides` if available.

    Inspect prints out data into `log` - standard python `logging` library with level `INFO`.

    :param object|function module: Module that should be inspected
    :param bool stream: if `True` then log out stats for every record otherwise (default) at the end
    :param int depth: how many submersions to do while printing out data
    """
    return Inspector(module, stream=stream, depth=depth)


class Inspector(object):
    """Inspect dataflow based on optional requires/provides and log out statistics as `INFO`.

    The inspector summarizes data structure into a comprehensive form because it takes into account
    that some structures will be wide.
    There is currently no change recording between rounds but will be added one day.

    :param bool stream: if `True` then log out stats for every record otherwise (default) at the end
    :param int depth: how many submersions to do while printing out data
    """

    class Metrics:
        """Enum of counter keys."""
        KEY = 0
        LEN = 1

    def __init__(self, module, stream=False, depth=3):
        self.name = Chain.module_name(module)
        self.requires = getattr(module, "requires", [])
        self.provides = getattr(module, "provides", [])
        self.relevant = self.requires + self.provides

        self._module = module
        self._stream = stream
        self._depth = depth
        self._process = getattr(module, "process", module)
        self._prev = None
        self._counters = [collections.Counter() for _ in range(2)]
        self._calls = 0
        self._structure = None

    def relevant_data(self, data):
        """Pick up only requires/provides keys if available."""
        if not self.relevant:
            return data
        return dict([(relevant, data[relevant]) for relevant in self.relevant])

    def process(self, data):
        self._calls += 1
        pre_keys = sorted(data.keys())
        self._process(data)
        post_keys = sorted(data.keys())
        self._counters[Inspector.Metrics.KEY]["{!s} -> {!s}".format(pre_keys, post_keys)] += 1
        relevant = self.relevant_data(data)

        for key, value in relevant.items():
            if hasattr(value, "__len__"):
                self._counters[Inspector.Metrics.LEN]["{}: {:d}".format(key, len(value))] += 1
        if self._structure is None:
            self._structure = dict([(key, self._inspect_structure(val)) for key, val in relevant.items()])
        # sledovat pamet pres psutils
        if self._prev is not None:
            self._inspect_changes(self._prev, data)
        self._prev = relevant
        if self._stream:
            self.print_log()

    def _inspect_structure(self, data, d=0):
        if d >= self._depth:
            if isinstance(data, dict) and len(data.keys()) > 10:
                key = list(data.keys())[0]

                return {
                    "{:d} keys of type {!s}; ex: ({!s})".format(len(data.keys()), type(key), key):
                        "{!s} ({!s})".format(type(data[key]), data[key])
                }
            if isinstance(data, (tuple, list)):
                if len(data) > 0:
                    return "[list of {!s}]".format(type(data[0]))
                return "[empty]"
            return data
        if isinstance(data, (list, tuple)):
            if len(data) > 0:
                return {"[len={:d}]".format(len(data)): self._inspect_structure(data[0], d + 1)}
            return {"[]": "empty"}
        if isinstance(data, dict):
            if len(data.keys()) > 10:
                # very likely a dist used as a list - inspenct only one item
                key = list(data.keys())[0]
                return {
                    "{!s}#{:d} times ({!s})".format(type(key), len(data.keys()), key):
                        self._inspect_structure(data[key], d + 1)
                }
            return dict([(key, self._inspect_structure(data[key], d + 1)) for key in data])
        return data

    def _inspect_changes(self, prev, curr):
        pass

    def print_log(self):
        log.info("Data flow structure")
        log.info(pprint.pformat(self._structure, indent=4, width=200))
        log.info("End of data flow structure")
        self._structure = None

    def close(self):
        if hasattr(self._module, "close"):
            self._module.close()
        if not self._stream:
            self.print_log()
