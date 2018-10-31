import logging
import warnings
import os
import six

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
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        root_logger.addHandler(stream_handler)

    warnings.simplefilter("once")


def _close_file_handlers():
    root_logger = logging.getLogger()
    for file_handler in root_logger.handlers:
        file_handler.close()
