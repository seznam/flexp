from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from copy import deepcopy, copy

import six
import collections
import time
import hashlib
import os
import inspect
from functools import partial
from six.moves import cPickle as pickle
import gc
import stat

from flexp.flow import Chain
from flexp.utils import get_logger


log = get_logger(__name__)


RWRWRW = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH
GB = 1024 ** 3


class PickleMixinP2(object):
    """Add pickling python2 functionality to any class."""

    def __init__(self, *args, **kwargs):
        self._pickler = pickle.Pickler(-1)
        self._pickler.fast = 1
        super(PickleMixinP2, self).__init__(*args, **kwargs)

    def pickle(self, obj, encode=False):
        if encode and isinstance(obj, six.text_type):
            obj = obj.encode("utf8")
        return self._pickler.dump(obj).getvalue()

    def unpickle(self, s):
        return pickle.loads(s)


class PickleMixinP3(object):
    """Add pickling python3 functionality to any class.

    Unfortunately unicode strings pickled by python2 cannot be reproduced in python3.
    """

    def pickle(self, obj, version=-1, encode=False):
        if encode and isinstance(obj, six.text_type):
            obj = obj.encode("utf8")  # convert all string into UTF-8
        return pickle.dumps(obj, version)

    def unpickle(self, s):
        try:
            return pickle.loads(s, encoding='utf-8')
        except UnicodeDecodeError:
            # fallback for very old mdbs
            return pickle.loads(s, encoding='bytes')


if six.PY3:
    PickleMixin = PickleMixinP3
else:
    PickleMixin = PickleMixinP2


class ObjectDumper(PickleMixin):
    """Functionality of this class is used in PickleCache and CachingChain"""

    def _object_dump_to_string(self, obj, max_recursion_level, level=0, debug_level=0):
        """Consolidate object with its attributes and their values into ony byte-string.
        If object has PickleCacheBlackList class attribute then attributes listed there are not taken into account.
        :param obj: Object instance
        :param int level: recursion level
        :param int debug_level: debug_level 0 (silence), 1 or 2 (full)
        :return: unicode String image of the pickled object
        """
        if level > max_recursion_level:
            return "".encode("ASCII")
        dump_string = obj.__class__.__name__.encode("ASCII")
        if debug_level == 2:
            print("\t"*level+"level: {}, class name {}".format(level, dump_string))
        if hasattr(obj, '__name__'):  # to distinguish functions from each other
            dump_string += obj.__name__.encode("ASCII")
            if debug_level == 2:
                print("\t"*level+"level: {}, function name {}".format(level, obj.__name__.encode("ASCII")))

        # Get insides of the objects, based on the type
        if isinstance(obj, str):
            if debug_level == 2:
                print("\t"*level+"level: {}, obj is str: {}".format(level, obj))
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
                    # Try to sort the items.
                    try:
                        items = [(str(i), o) for i, o in enumerate(sorted(obj))]
                    except:
                        # After all fails, do not sort the insides, but this can be bad.
                        # Print log that this happens.
                        items = [(str(i), o) for i, o in enumerate(obj)]
                        if len(items) > 0:
                            log.debug("Can't sort insides of object type {}, first element is {}".format(obj.__class__.__name__, items[0][1].__class__.__name__))

        if debug_level == 2:
            print("\t"*level+"level: {}, items: {}".format(level, items))
        for attribute, value in items:
            try:
                if debug_level == 2:
                    print("\t" * level + "level: {}, attribute: {}".format(level, attribute))
                try:
                    add_string = self._object_dump_to_string(attribute, max_recursion_level, level + 1, debug_level)
                except:
                    add_string = self.pickle(attribute)
                dump_string += add_string
            except pickle.PicklingError:  # attribute could not be dumped
                pass

            try:
                if debug_level == 2:
                    print("\t" * level + "level: {}, value: {}".format(level, value))
                try:
                    add_string = self._object_dump_to_string(value, max_recursion_level, level + 1, debug_level)
                except:
                    add_string = self.pickle(value)
                dump_string += add_string
            except pickle.PicklingError:  # attribute could not be dumped
                pass

        if debug_level > 0 and level == 0:
            print("dump_string is {}\n"
                  "Compare this with another cache hash with command\n"
                  " $ cmp -bl <(echo -n abcda) <(echo -n aqcde)".format(hashlib.sha256(six.binary_type().join([dump_string])).hexdigest()))

        return dump_string


class PickleCache(Chain, ObjectDumper):
    """
    Caches the data processed by the given chain. Cached data are stored in the given directory as pickle files.
    File names are the hash od data.id and chain hash.
    """

    def __init__(self, directory, data_key="id", chain=None, force=False,
                 max_recursion_level=10, dir_rights=0o777, debug_level=0, save_cache=True):
        """

        :param directory:
        :param data_key:
        :param chain:
        :param boolean force: if True then will not read the cache
        :param max_recursion_level:
        :param dir_rights:
        :param int debug_level:
        :param boolean force: if True then will dump the cache
        """
        super(PickleCache, self).__init__(chain)
        self.directory = directory
        self.force = force
        self.data_key = data_key
        self.max_recursion_level = max_recursion_level
        self.debug_level = debug_level

        self.chain_info = {'chain_len': 0, 'chain_hash': None,
                           'chain_mtime': None,
                           'chain_repr': None}
        self.save_cache = save_cache
        # update chain info
        if chain is not None:
            self.hash_chain()

        if not os.path.exists(directory):
            # Override umask settings to enforce flexible rights. 777 enables collaboration between people and prevents
            # omnipresent AccessDeniedErrors.
            original_umask = None
            try:
                original_umask = os.umask(0)
                os.makedirs(directory, dir_rights)
            finally:
                if original_umask is not None:
                    os.umask(original_umask)

    def step(self, data):
        # TODO write step method or get rid of step altogether, as Inspector is not much used
        pass

    def get_cache_file_from_id(self, data_id):
        key = hashlib.sha256(self.pickle(data_id)).hexdigest()
        return self.directory + "/" + key + self.chain_info['chain_hash']

    def get_cache_file(self, data):
        key = hashlib.sha256(self.pickle(data[self.data_key])).hexdigest()
        chain_hash = self.chain_info['chain_hash']
        return self.directory + "/" + key + chain_hash

    def check_cache_exists(self, data):
        """
        :type data: dict
        :rtype: bool
        """
        file = self.get_cache_file(data)
        log.debug("Cache: {}".format(file))
        return os.path.exists(file)

    @staticmethod
    def hash_dump_string(dump_string):
        """
        Takes unicode string and create sha256 hash
        :param dump_string:
        :return string:
        """
        return hashlib.sha256(six.binary_type().join([dump_string])).hexdigest()
      
    def _get_chain_hash(self, chain):
        """Create a unique hash for each chain configuration.

        It takes into account values of inner attributes of each object.
        :param chain: list of modules
        :return: string
        """
        # todo if like this then PickleCache(m1, m2) + PickleCache(m3) != PickleCache(m1, m2, m3)
        chain_string = self._object_dump_to_string(chain, self.max_recursion_level, debug_level=self.debug_level)
        return self.hash_dump_string(chain_string)

    def _get_object_mtime(self, obj):
        """Extract mtime from object's source file.

        :param obj: Object instance
        :return: float Time of the last modification of the source file on an object
        """
        try:
            mtime = os.path.getmtime(inspect.getsourcefile(obj.__class__))
        except (TypeError, OSError):
            mtime = 0.
        return mtime

    def _get_chain_mtime(self, chain):
        """Count time of the last modification of each module and returns their maximum.

        :param chain: list of modules
        :return: float
        """
        chain_mtimes = [0.]  # default time in case no other time is obtained
        for module in chain:
            if isinstance(module, collections.Iterable):  # module is a chain
                chain_mtimes.append(self._get_chain_mtime(module))
            elif hasattr(module, 'process'):  # module is an object
                chain_mtimes.append(self._get_object_mtime(module))
            else:  # module is a function
                # no time is obtained because the function may be in the main file and its mtime might be undesirable
                pass
        return max(chain_mtimes)

    def _get_chain_repr(self, chain):
        """Concatenate string representations of all modules in the chain.

        :param chain: list of modules
        :return: string
        """
        chain_repr = []
        for module in chain:
            if isinstance(module, collections.Iterable):  # module is a chain
                chain_repr.append(self._get_chain_repr(module))
            elif hasattr(module, 'process'):  # module is an object
                chain_repr.extend(
                    (str(module.__class__), repr(vars(module))))
            else:  # module is a function
                if isinstance(module, partial):  # partial function
                    chain_repr.extend((str(module.__class__), repr(module.func),
                                       repr(module.keywords)))
                else:
                    chain_repr.append(repr(module))
        return ' '.join(chain_repr)

    def _process(self, data, cache):
        """Process data and puts them to structure for caching.

        :param data: dict
        :param cache: dict Caching structure
        :return: (dict, bool)
        """
        stop = False
        try:
            super(PickleCache, self).process(data)
        except StopIteration:
            stop = True

        data_to_save = data

        cache = dict() if cache is None else cache
        cache[self.chain_info['chain_hash']] = {"data": data_to_save,
                                                "stopped": stop,
                                                'chain_repr': self.chain_info[
                                                    'chain_repr'],
                                                'chain_mtime': self.chain_info[
                                                    'chain_mtime']}
        return cache, stop

    def _check_time_consistency(self, cache_mtime, chain_mtime):
        """Check whether modification times correspond.

        :param cache_mtime: float Modification time of modules by which cached data were processed
        :param chain_mtime: float Modification time of modules in chain
        """
        if cache_mtime != chain_mtime:
            log.warn("""Modification times do not correspond.
            Last change of chain: {}
            Last change in cache: {}""".format(time.ctime(chain_mtime),
                                               time.ctime(cache_mtime)))

    def hash_chain(self):
        """Hash the chain in order to use the hash as a dictionary key."""
        if len(self.modules) != self.chain_info['chain_len']:
            self.chain_info = {
                'chain_len': len(self.modules),
                'chain_mtime': self._get_chain_mtime(self.modules),
                'chain_hash': self._get_chain_hash(self.modules),
                'chain_repr': self._get_chain_repr(self.modules),
            }

    @property
    def chain_hash(self):
        """Return chain_hash of the current chain."""
        return self.chain_info['chain_hash']

    def process(self, data):
        """
        Checks if there is cached data. If so, returns it, otherwise runs the chain and stores the processed data.
        :type data: dict
        :return:
        """
        file = self.get_cache_file(data)
        loaded = False
        if self.check_cache_exists(data):
            if self.force:
                log.info("Item found in cache but force=True")
            else:
                try:
                    log.info("Found in cache, skipping chain")
                    with open(file, 'rb') as f:
                        # https://stackoverflow.com/questions/2766685/how-can-i-speed-up-unpickling-large-objects-if-i-have-plenty-of-ram/36699998#36699998
                        # disable garbage collector for speedup unpickling
                        gc.disable()
                        cache = pickle.load(f)

                        # enable garbage collector again
                        gc.enable()

                    retrieved_data = cache['data']
                    stop = cache["stopped"]
                    if stop:
                        raise StopIteration()
                    self._check_time_consistency(cache['chain_mtime'],
                                                 self.chain_info['chain_mtime'])
                    for key, value in retrieved_data.items():
                        data[key] = value
                    loaded = True
                except EOFError:
                    log.warning(
                        "Failed to load cache item {} (corrupted file will be deleted)".format(file))
                    os.unlink(file)
        if not loaded:
            log.debug("Not found in cache, processing chain")
            cache, stop = self._process(data, {})
            cache = cache[self.chain_info['chain_hash']]
            if self.save_cache:
                with open(file, 'wb') as f:
                    try:
                        pickle.dump(cache, f, protocol=4)
                    except:
                        pickle.dump(cache, f)

            # Try to set some more flexible access rights
            try:
                os.chmod(file, RWRWRW)
            except OSError:
                pass

    def close(self):
        """Close cache and chain."""
        super(PickleCache, self).close()
