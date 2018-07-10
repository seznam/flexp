from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from collections import defaultdict
import copy

from flexp.utils import parallelize, merge_dicts
from flexp.flow import Chain
from flexp.utils import get_logger


log = get_logger(__name__)


def stop(data):
    """Stop chain processing.

    @param data dict
    """
    raise StopIteration()


class ParallelDataChain:
    """
    Chain that runs all the data through the chain in parallel. Expects array of data on input.
    Example:

    from flow import ParallelDataChain
    cross_val_data = [{"data":1},{"data":2},{"data":3},{"data":4},{"data":5}]
    import copy
    chain = ParallelDataChain(max_processes=5, chain=[
        Fit("rfreg_10_6", RandomForestRegressor(n_estimators=10, max_depth=6)),
        Predict()
    ])
    chain.process(cross_val_data)
    # In each of the five folds, there are predictions from random forest
    for fold_data in cross_val_data:
        print(fold_data["predictions"]["rfreg_10_6"])

    """

    def __init__(self, chain=None, max_processes=5, copy_chain=False):
        """
        Sets up chain
        @param copy_chain: bool If true, the chain will be copy.copyied
        """
        self.chain = Chain(chain)
        self.max_processes = max_processes
        self.copy_chain = copy_chain

    def process(self, data):
        """
        Processes chain
        @param data dict
        """
        log.debug("ParallelDataChain: Starting")

        def process_calibration(data):
            id_, data2 = data
            log.info("Processing parallel data {}".format(id_))
            if self.copy_chain:
                chain = copy.deepcopy(self.chain)
            else:
                chain = self.chain
            chain.process(data2)
            return id_, data2

        # run through all examples
        all_data = [d for d in parallelize(process_calibration,
                                           [(i, data[i]) for i in
                                            range(len(data))],
                                           self.max_processes)]

        # Reassign new data to old data
        for id_, new_data in sorted(all_data):
            data[id_] = new_data

        log.debug("ParallelDataChain: Ended")


class ParallelModuleChain(Chain):
    """
    Chain that runs all modules in parallel on the same data. It requires a list of keys to pass to the new processes
    and a list of keys to retrieve from finished processes.
    Example:

    from flow import ParallelModuleChain
    chain = ParallelModuleChain(input_keys=["trainset", "testset", "mfs"], output_keys=["models"],max_processes=5,
        chain = [
             Fit("etreg_50_10", ExtraTreesRegressor(n_estimators=50, max_depth=10)),
             Fit("rfreg_50_10", RandomForestRegressor(n_estimators=50, max_depth=10)),
             ...
         ]
    ])
    chain.process(data)

    """

    def __init__(self, input_keys=None, output_keys=None, chain=None,
                 max_processes=5, conflict_operation=None):
        """
        Sets up chain
        """
        super(ParallelModuleChain, self).__init__(chain)
        self.max_processes = max_processes
        self.input_keys = ["trainset"] if input_keys is None else input_keys
        # This is right - fill output_keys with input_keys if not defined explicitly
        if output_keys is None:
            self.output_keys = input_keys
        else:
            self.output_keys = output_keys
        self.conflict_operation = conflict_operation

    def process(self, data):
        """
        Processes chain
        @param data dict
        """
        log.debug("ParallelModuleChain: Starting")
        log.debug("ParallelModuleChain: Creating shared dict")

        data_parallel = defaultdict(dict)
        for key in self.input_keys:
            data_parallel[key] = data.get(key, defaultdict(dict))

        log.debug("ParallelModuleChain: Starting parallel computation.")

        def process_calibration(data):
            module, data2 = data
            module.process(data2)
            return data2

        all_data = [d for d in parallelize(process_calibration,
                                           [(self.modules[i], data_parallel) for
                                            i in range(len(self.modules))],
                                           self.max_processes)]
        log.debug(
            "ParallelModuleChain: Parallel run done, now copying to original dict.")
        for key in self.output_keys:
            if key not in data:
                data[key] = defaultdict(dict)
            for d in all_data:
                try:
                    if (data[key] == d[key]).all():
                        continue
                except:
                    try:
                        if data[key] == d[key]:
                            continue
                    except:
                        pass
                merge_dicts(data[key], d[key],
                            conflict_operation=self.conflict_operation)
        log.debug("ParallelModuleChain: Ended")
