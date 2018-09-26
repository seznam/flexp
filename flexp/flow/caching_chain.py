from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import collections
import hashlib
import pickle
import time
import types
from copy import copy

import six

from flexp.flow import Chain
from flexp.flow.cache import PickleCache, ObjectDumper
from flexp.utils import get_logger


log = get_logger(__name__)


def hash_dump_string(dump_string):
    """
    Takes unicode string and create sha256 hash
    :param dump_string:
    :return:
    """
    return hashlib.sha256(six.binary_type().join([dump_string])).hexdigest()


class CachingChain(Chain, ObjectDumper):
    """Chains of modules run by `process` function.
    Update data id after each module with parameter UPDATE_ID = True
    """

    def __init__(self, chain=None, check=False, name=None, ignore_first_module_requirements=True, update_data_id='id',
                 max_recursion_level=10):
        """Set up modules.
        :param list[object|function]|object|function chain: one module or
        list of modules
        :param bool check: check if chain modules are compatible
        :param bool ignore_first_module_requirements: First module
        requirements may be satisfied by input data therefore it is common to
        not check them
        :param str name:
        """
        self.id_hashes = []
        self.update_data_id = update_data_id
        self.max_recursion_level = max_recursion_level
        super().__init__(chain, check, name, ignore_first_module_requirements)

    def _add(self, module):
        """Add module to the chain
        Check if a new module conforms to our requirements.

        :param object|function module:
        """
        super()._add(module)
        if isinstance(module, PickleCache):
            # no need to distinguish PickleCache(chain=[Module1, Module2]) and [Module1, Module2]
            # PickleCache.chain_info['chain_hash'] created same way: hash_dump_string(object_dump_to_string([module]))
            # content of chain_hash (which modules are used) is controlled by PickleCache logic
            # assume that PickleCache contains only modules that have significant impact on data
            self.id_hashes.append(module.chain_info['chain_hash'])
        else:
            # todo use PickleCache  Function
            # todo which will control UpdateDataId
            if hasattr(module, 'UpdateDataId'):
                self.id_hashes.append(hash_dump_string(self._object_dump_to_string([module], self.max_recursion_level)))
            else:
                self.id_hashes.append("")

    def update_data_id_func(self, data, new_hash):
        """
        Data id is `some_data_id_hash|modules_hash`
        :param data:
        :param new_hash:
        :return:
        """

        # print("id before", getattr(data, self.update_data_id))
        data_id = getattr(data, self.update_data_id)
        if hasattr(data, 'id'):
            parts = data_id.split("|")
            if len(parts) > 1:
                prefix = "".join(parts[:-1])
                old_hash = parts[-1]
            else:
                prefix = data_id
                old_hash = ""
            updated_hash = hashlib.sha256((old_hash+new_hash).encode()).hexdigest()
            setattr(data, self.update_data_id, prefix + "|" + updated_hash)
            # print("".join(data.id.split("|")[:-1]), updated_hash)
        else:
            setattr(data, self.update_data_id, new_hash)
        # print("id after", getattr(data, self.update_data_id))
        log.debug("Data.id updated: data.id")

    def process(self, data):
        """Run all modules.

        :param dict data: the inplace processed data - one data per call
        :return: dict:
        """
        for i in range(len(self.modules)):
            try:
                if hasattr(self.modules[i], "process"):
                    log.debug("{}.process()".format(self.names[i]))
                    process_func = self.modules[i].process
                else:
                    log.debug("{}()".format(self.names[i]))
                    process_func = self.modules[i]
                start = time.clock()
                process_func(data)
                if self.id_hashes[i]:
                    # after each module process
                    self.update_data_id_func(data, self.id_hashes[i])
                    # log.debug(data.id)
                end = time.clock()
                self.times[i] += (end - start)
            except StopIteration:
                log.debug("{} requested stop. Processing stopped".format(
                    self.names[i]))
                raise
        self.iterations += 1

