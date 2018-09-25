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
from flexp.flow.cache import PickleCache
from flexp.utils import get_logger


log = get_logger(__name__)


def hash_dump_string(dump_string):
    """
    Takes unicode string and create sha256 hash
    :param dump_string:
    :return:
    """
    return hashlib.sha256(six.binary_type().join([dump_string])).hexdigest()


def pickle_obj(obj, version=-1, encode=False):
    if encode and isinstance(obj, six.text_type):
        obj = obj.encode("utf8")  # convert all string into UTF-8
    return pickle.dumps(obj, version)


def unpickle_obj(s):
    try:
        return pickle.loads(s, encoding='utf-8')
    except UnicodeDecodeError:
        # fallback for very old mdbs
        return pickle.loads(s, encoding='bytes')


def object_dump_to_string(obj, level=0, debug_level=0, max_recursion_level=10):
    """Consolidate object with its attributes and their values into ony byte-string.
    If object has PickleCacheBlackList class attribute then attributes listed there are not taken into account.

    :param obj: Object instance
    :param int level: recursion level
    :param int debug_level: debug_level 0 (silence), 1 or 2 (full)
     :return: unicode String image of the pickled object
    """
    if level > max_recursion_level:
        return ""

    dump_string = obj.__class__.__name__.encode("ASCII")
    if debug_level == 2:
        print("\t" * level + "level: {}, class name {}".format(level, dump_string))

    if hasattr(obj, '__name__'):  # to distinguish functions from each other
        dump_string += obj.__name__.encode("ASCII")
        if debug_level == 2:
            print("\t" * level + "level: {}, function name {}".format(level, obj.__name__.encode("ASCII")))

    # Get insides of the objects, based on the type

    if isinstance(obj, str):
        if debug_level == 2:
            print("\t" * level + "level: {}, obj is str: {}".format(level, obj))
        return dump_string + obj
    else:
        try:
            items = copy(vars(obj))
            if hasattr(obj, 'PickleCacheBlackList'):
                if debug_level == 2:
                    print("\t" * level + "obj has blacklist", obj.PickleCacheBlackList)
                for v in obj.PickleCacheBlackList:
                    del items[v]

            items = sorted(items.items())
        except:
            try:
                items = sorted(obj.items())
            except:
                items = [(str(i), o) for i, o in enumerate(obj)]

    if debug_level == 2:
        print("\t" * level + "level: {}, items: {}".format(level, items))
    for attribute, value in items:
        # TODO checkpoints
        # TODO check for checkpoints
        try:
            if debug_level == 2:
                print("\t" * level + "level: {}, attribute: {}".format(level, attribute))
            try:
                add_string = object_dump_to_string(attribute, level + 1, debug_level)
            except:
                add_string = pickle_obj(attribute)
            dump_string += add_string
        except pickle.PicklingError:  # attribute could not be dumped
            pass

        try:
            if debug_level == 2:
                print("\t" * level + "level: {}, value: {}".format(level, value))
            try:
                add_string = object_dump_to_string(value, level + 1, debug_level)
            except:
                add_string = pickle_obj(value)
            dump_string += add_string
        except pickle.PicklingError:  # attribute could not be dumped
            pass

    if debug_level > 0 and level == 0:
        print("dump_string is {}\n"
              "Compare this with another cache hash with command\n"
              " $ cmp -bl <(echo -n abcda) <(echo -n aqcde)".format(hash_dump_string(dump_string)))

    return dump_string


class CachingChain(Chain):
    """Chains of modules run by `process` function.
    Update data id after each module with parameter UPDATE_ID = True
    """

    def __init__(self, chain=None, check=False, name=None, ignore_first_module_requirements=True, update_data_id='id'):
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
            self.id_hashes.append(module.chain_info['chain_hash'])
        else:
            # todo use PickleCache  Function
            # todo which will control UpdateDataId
            if hasattr(module, 'UpdateDataId'):
                self.id_hashes.append(hash_dump_string(object_dump_to_string([module])))
            else:
                self.id_hashes.append("")
        # print("_add", self.id_hashes[-1])

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
