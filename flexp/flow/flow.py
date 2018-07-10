from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import collections
import time
import types

from flexp.utils import get_logger


log = get_logger(__name__)


class Chain(object):
    """Chains of modules run by `process` function."""

    def __init__(self, chain=None, check=False, name=None,
                 ignore_first_module_requirements=True):
        """Set up modules.
        :param list[object|function]|object|function chain: one module or
        list of modules
        :param bool check: check if chain modules are compatible
        :param bool ignore_first_module_requirements: First module
        requirements may be satisfied by input data therefore it is common to
        not check them
        :param str name:
        """
        self.names = []
        self.modules = []
        self.times = []
        self.iterations = 0
        self.requires = set()
        self.provides = set()
        self._check = check
        self._ignore_first_module_requirements = \
            ignore_first_module_requirements
        self._base_name = name if name else self.__class__.__name__
        super(Chain, self).__init__()
        self._generate_name()
        self.add(chain)

    def __enter__(self):
        """Return self to with statement."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Call module finalizers."""
        self.close()

    def __iter__(self):
        return iter(self.modules)

    def __str__(self):
        """Describe Chain

        :return: str
        """
        return self.name

    def add(self, module):
        """Add module to modules.

        :param list[object|function]|object|function module: one module or
        list of modules
        """
        if not module:
            return
        if isinstance(module, collections.Iterable):
            for m in module:
                self._add(m)
        else:
            self._add(module)
        self._generate_name()

    def _generate_name(self):
        self.name = "{}[{}]".format(self._base_name, "-".join(self.names))

    def _add(self, module):
        """Add module to the chain
        Check if a new module conforms to our requirements.

        :param object|function module:
        """
        if not (isinstance(module, types.FunctionType) or
                hasattr(module, 'process')):
            raise AttributeError(
                "No 'process' method in {}".format(self.module_name(module)))
        self.names.append(self.module_name(module))
        self.modules.append(module)
        self.times.append(0.0)
        if not (self._ignore_first_module_requirements and
                len(self.modules) == 1):
            self.requires.update(getattr(module, "requires", []))
        self._check_consistency(module=module)
        self.provides.update(getattr(module, "provides", []))

    def _check_consistency(self, module=None):
        """Check modules consistency."""
        if not self._check:
            return True
        missing = self.requires - self.provides
        if missing:
            raise KeyError(
                "Module: {} - Required keys '{}' not satisfied.".format(
                    self.module_name(module), missing))

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
                end = time.clock()
                self.times[i] += (end - start)
            except StopIteration:
                log.debug("{} requested stop. Processing stopped".format(
                    self.names[i]))
                raise
        self.iterations += 1

    def close(self):
        """Call module finalizers."""
        for i in range(len(self.modules)):
            if hasattr(self.modules[i], "close"):
                self.modules[i].close()
            self.times[i] /= self.iterations if self.iterations > 0 else 1
            log.info("{} average execution time {:.2f} sec".format(
                self.names[i], self.times[i]))

    @staticmethod
    def module_name(module):
        """Return name of the module.

        :param object|function module:
        :return unicode
        """
        # user defined property
        if hasattr(module, "name"):
            return module.name
        # function
        if isinstance(module, types.FunctionType):
            return module.__name__
        # object
        if hasattr(module, "__class__"):
            return module.__class__.__name__
        # default
        return module.__name__
