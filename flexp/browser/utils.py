"""Utils used only in browser: include html, etc.

"""
from __future__ import unicode_literals
import logging
from os import stat
from os.path import exists
import warnings

from flexp.flexp.logging import get_loglevel_from_env, log_formatter


def message(text):
    return """<div class='w3-border'>
                <div class='w3-leftbar w3-border-orange w3-container'>
                  <p><strong>Warning:</strong> {message} </p>
                </div>
              </div>""".format(message=text)


def get_link_to_file(title, href, max_file_size_byte=10000000, path_to_file=None):
    """Create HTML the link to the file.

    :param title:
    :param href:
    :param max_file_size_byte: if file size > maxFileSize, it returns only title, not link
            If None, returns link all the time
            To prevent freezing browser when too large data
    :param path_to_file:
    :return: link to file, or title if file size > maxFileSize
    """
    if max_file_size_byte is not None and path_to_file is not None and exists(path_to_file):
        file_stat = stat(path_to_file)
        size = file_stat.st_size
        if size > max_file_size_byte and not path_to_file.endswith(".zip"):
            return title  # Too large file, don't link it
    return "<a href='{href}'>{title}</a>".format(href=href, title=title)


def setup_logging(level=logging.DEBUG):
    level = get_loglevel_from_env(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    root_logger.addHandler(stream_handler)
    warnings.simplefilter("once")
