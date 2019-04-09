from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import hashlib
import os
import timeit

from flexp.flow import Chain
from flexp.flow.cache import PickleCache, ObjectDumper
from flexp.utils import get_logger


log = get_logger(__name__)


class CachingChain(Chain, ObjectDumper):
    """Chains of modules run by `process` function.
    Update data id after each module with parameter UpdateAttrName = 'UpdateDataId'.
    Look for last prepared PickleCache and skip previous modules
    """

    UpdateAttrName = 'UpdateDataId'

    SEPARATOR = "|"

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
            if hasattr(module, self.UpdateAttrName):
                self.id_hashes.append(PickleCache.hash_dump_string(self._object_dump_to_string([module], self.max_recursion_level)))
            else:
                self.id_hashes.append("")

    def get_updated_data_ids(self, data):
        """
        Create list of data ids of length = len(self.modules) + 1 , i-th id is input for i-th module
        :param data:
        :return list[str]: list of data ids
        """
        data_id = getattr(data, self.update_data_id)
        updated_ids = [data_id]
        for i, module in enumerate(self.modules):
            if self.id_hashes[i]:

                parts = data_id.split(self.SEPARATOR)
                if len(parts) > 1:
                    prefix = "".join(parts[:-1])
                    old_hash = parts[-1]
                else:
                    prefix = data_id
                    old_hash = ""
                updated_hash = hashlib.sha256((old_hash + self.id_hashes[i]).encode()).hexdigest()
                updated_ids.append(prefix + self.SEPARATOR + updated_hash)
            else:
                updated_ids.append(updated_ids[-1])
            data_id = updated_ids[-1]
        return updated_ids

    def process(self, data):
        """Run all modules.

        :param dict data: the inplace processed data - one data per call
        :return: dict:
        """
        start = 0
        updated_ids = self.get_updated_data_ids(data)
        for i, module in list(enumerate(self.modules))[::-1]:
            if isinstance(module, PickleCache):
                # key = hashlib.sha256(self.pickle(updated_ids[i])).hexdigest()
                file = module.get_cache_file_from_id(updated_ids[i])
                if os.path.exists(file):
                    log.debug("We skip first {} modules because cache: {} exists".format(i, file))
                    start = i
                    break
        for i in range(start, len(self.modules)):
            try:
                if hasattr(self.modules[i], "process"):
                    log.debug("{}.process()".format(self.names[i]))
                    process_func = self.modules[i].process
                else:
                    log.debug("{}()".format(self.names[i]))
                    process_func = self.modules[i]
                start = timeit.default_timer()
                # update data ket from list before running module
                setattr(data, self.update_data_id,  updated_ids[i])
                process_func(data)
                end = timeit.default_timer()
                self.times[i] += (end - start)
            except StopIteration:
                log.debug("{} requested stop. Processing stopped".format(
                    self.names[i]))
                raise
        self.iterations += 1
