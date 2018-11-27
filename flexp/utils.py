import importlib.machinery
import logging

import shutil
from multiprocessing import Process, Queue, Pool
import random
import re
import string


def import_by_filename(name, module_path):
    """
    Import module by path. Module would appear in sys.modules
    :param name: str The name of the module that this loader will handle.
    :param module_path: str The path to the source file.
    :return:
    """
    return importlib.machinery.SourceFileLoader(name, module_path).load_module()


def clean_experiment_folder(folder):
    """Remove subdirectories and files below. Should be used when flexp is setup to clean experiment folder
    :param str folder:
    """
    import os
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def merge_dicts(a, b, path=None, conflict_operation=None):
    """
    Merges b into a
    :param dict a:
    :param dict b:
    :param None|list path: Path in dict structure
    :param conflict_operation:
    :return dict
    """

    if path is None:
        path = []

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)],
                            conflict_operation)
            else:
                try:
                    # same leaf value for numpy
                    if (a[key] == b[key]).all():
                        continue
                except:
                    pass
                try:
                    # same leaf value
                    if a[key] == b[key]:
                        continue
                except:
                    pass
                if not conflict_operation:
                    raise ValueError(
                        'Conflict at %s' % '.'.join(path + [str(key)]))
                else:
                    a[key] = conflict_operation(a[key], b[key])
        else:
            a[key] = b[key]

    return a


def natural_sort(seq):
    def _alphanum(x):
        return [int(x) if x.isdigit() else x.lower()
                for c in re.split('([0-9]+)', x)]

    return sorted(seq, key=_alphanum)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    Return random string of size
    @param size: int Length of returned string
    @param chars: list List of allowed chars
    @return: str Random string ex: "AJD45S"
    """
    return ''.join(random.choice(chars) for _ in range(size))


# -------------------------------------- Parallelizations, Multiprocessing --------------------------------------------


def parallelwork(fn, inputq, outputq):
    """Run unary `fn` in parallel on data taken from `inputq` and save results to `outputq`.

    :param fn: function
    :param inputq: multiprocessing.Queue
    :param outputq: multiprocessing.Queue
    """
    while True:
        i, x = inputq.get()
        if i is None:
            break
        try:
            outputq.put((i, fn(x)))
        except StopIteration:
            outputq.put((None, None))


def parallelize(fn, iterator, workers, queuesize_per_worker=None):
    """Parallize function call on items from the iterator.

    :param fn: function
    :param iterator: iterator
    :param workers: int
    :param queuesize_per_worker: int
    """

    # Try using imap
    try:
        # start n worker processes
        with Pool(processes=workers) as pool:
            # Use chunk size if got as parameter
            if queuesize_per_worker is not None:
                i = pool.imap(fn, iterator, queuesize_per_worker)
            else:
                i = pool.imap(fn, iterator)

            for res in i:
                yield res
    except:
        # todo this probably should be used when pool is not present?
        if queuesize_per_worker is not None:
            inputq = Queue(queuesize_per_worker * workers)
        else:
            inputq = Queue()
        outputq = Queue()

        processes = [Process(target=parallelwork, args=(fn, inputq, outputq))
                     for worker in range(workers)]

        for process in processes:
            process.daemon = True
            process.start()

        sent = [inputq.put((i, x)) for i, x in enumerate(iterator)]
        [inputq.put((None, None)) for worker in range(workers)]

        for n in range(len(sent)):
            i, x = outputq.get()
            if i is None:
                continue
            yield x

        [process.join() for process in processes]


def log_method(log_fnc=logging.debug, arguments=True):
    """Decorator to log the method's call with timing.

    :param log_fnc: {(str)->None} logging function (e.g. logger.debug or print)
    :param arguments: bool - True if you want to include arguments, False if not
    :returns: decorator
    """

    def wrap(fnc):
        def inner(*args, **kwargs):
            result = None
            log_fnc(u"Method call: {}.{}".format(fnc.__module__, fnc.__name__))
            if arguments:
                log_fnc(u"Arguments: args: {!s}, kwargs: {!s}".format(args, kwargs))
                result = fnc(*args, **kwargs)
            log_fnc(u"Method finished: {}.{}".format(fnc.__module__, fnc.__name__))
            return result

        return inner

    return wrap


def get_logger(name):
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    return logger


class PartialFormatter(string.Formatter):
    """
    Fills formating fields without provided values with `missing` value.
    Code from: https://stackoverflow.com/a/20250018/6579599
    """

    def __init__(self, missing='~', bad_fmt='!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value == None: return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise


def exception_safe(fcn, return_on_exception=None):
    """
    Function wrapper that handles exception by printing in log
    :param function fcn: Function to wrap
    :param Any return_on_exception: What should be returned if exception occures
    :return Any: If no exception returns the same as `fcn`, otherwise returns `return_on_exception`
    """
    def wrapper(*args, **kwargs):
        try:
            return fcn(*args, **kwargs)
        except Exception as e:
            logging.warning("Exception in {}: {}".format(fcn.__name__, e))
            return return_on_exception

    return wrapper
