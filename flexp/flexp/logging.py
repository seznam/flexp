import logging
import warnings
import os
import six

from tqdm import tqdm


log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def loglevel_from_string(level):
    """
    >>> _loglevel_from_string('debug')
    10
    >>> _loglevel_from_string(logging.INFO)
    20
    """

    if isinstance(level, str):
        level = getattr(logging, level.upper())
        assert isinstance(level, six.integer_types)
    return level


def get_loglevel_from_env(default_level):
    """
    >>> os.environ['FLEXP_LOGLEVEL'] = 'info'
    >>> get_loglevel_from_env(logging.DEBUG)
    20
    >>> del os.environ['FLEXP_LOGLEVEL']
    >>> get_loglevel_from_env(logging.DEBUG)
    10
    """
    flexp_loglevel = os.environ.get('FLEXP_LOGLEVEL')
    if flexp_loglevel is not None:
        loglevel = flexp_loglevel
    else:
        loglevel = default_level
    return loglevel_from_string(loglevel)


class TqdmLoggingHandler(logging.Handler):
    """
    credit: https://stackoverflow.com/questions/38543506/change-logging-print-function-to-tqdm-write-so-logging-doesnt-interfere-wit
    """
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def _setup_logging(level=logging.DEBUG, filename='log.txt', disable_stderr=False):
    _close_file_handlers()
    level = loglevel_from_string(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if filename is not None:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
    if not disable_stderr:
        tqdm_handler = TqdmLoggingHandler() # logging.StreamHandler()
        tqdm_handler.setFormatter(log_formatter)
        root_logger.addHandler(tqdm_handler)

    warnings.simplefilter("once")


def _close_file_handlers():
    root_logger = logging.getLogger()
    for file_handler in root_logger.handlers:
        file_handler.close()
    root_logger.handlers = []
