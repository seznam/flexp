from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import shutil
from datetime import datetime
from shutil import copyfile, copystat
import io
import stat
import os
import sys
import six
import os.path
import atexit
import zipfile
import logging

from flexp.flexp.logging import _setup_logging, _close_file_handlers
from flexp.utils import get_logger

log = get_logger(__name__)

RWXRWS = stat.S_IRWXU | stat.S_IRWXG | stat.S_ISGID
RWRWR = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH
RWXRWXRWX = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH

_eh = {}


class ExperimentHandler(object):
    """Class handling experiment."""

    METADATA_FILE_PATH = "flexp_info.txt"
    SUCCESS_PATH = ".SUCCESS"
    FAIL_PATH = ".FAIL"

    def __init__(self, default_rights=RWXRWS):
        self._setup = False

        self._root_dir = None
        self._name = None
        self._with_date = False
        self._date_str = ""

        self._expdir = None

        self._metadata = dict()
        self._start_time = None

        self.disabled = False
        self.default_rights = default_rights

        # exit reason info
        self._exit_code = 0
        self._exception = None
        self._orig_exit = sys.exit
        sys.exit = self._exit
        sys.excepthook = self._exc_handler
        self._traceback = None

    def _exit(self, code=0):
        self._exit_code = code
        self._orig_exit(code)

    def _exc_handler(self, exc_type, exc, tb, *args):
        self._exc_type = exc_type
        self._exception = exc
        self._traceback = tb

    @property
    def name(self):
        return self._name

    def setup(self, root_dir, exp_name=None, with_date=False):
        """
        Setup ExperimentHandler.

        Can be called many times during one execution.

        :param root_dir: Path to experiments root directory. New directories will be created in the folder.
        :param exp_name: Name of the parameter, will be used for new folder creation.
        :param with_date: True, if you want to include datetime in the experiment's dir name

        :return: None
        """
        self._set_root_dir(root_dir)
        self._set_name(exp_name or os.getlogin())

        datetime_str = "{:%Y-%m-%d-%H-%M-%S}".format(datetime.now())

        if with_date or exp_name is None:
            self._date_str = "_" + datetime_str

        if not os.path.isdir(self.get_experiment_dir()) and not self.disabled:
            try:
                os.chmod(self._root_dir, self.default_rights)
            except OSError:
                log.warning("could not add group+write to experiment root dir " + self._root_dir)
            os.makedirs(self.get_experiment_dir())
            os.chmod(self.get_experiment_dir(), self.default_rights)

        self._start_time = datetime_str

    def _unicodize(self, txt):
        if isinstance(txt, six.binary_type):
            return txt.decode("utf-8")
        return txt

    def _write_metadata(self):
        """Write collected metadata to the file.

        :return: None
        """
        if self.disabled:
            return

        if self._start_time is None:
            # setup was not run
            return

        if not os.path.exists(self.get_experiment_dir()):
            # somebody deleted experiment directory before quitting - do not fail
            return

        with io.open(self.get_file_path(self.METADATA_FILE_PATH), "w", encoding="utf-8") as fout:
            fout.write(u"Start time: " + self._start_time + "\n")
            fout.write(u"End time: " + u"{:%Y-%m-%d-%H-%M-%S}".format(datetime.now()) + "\n")
            fout.write(u"Command: python " + u" ".join(map(self._unicodize, sys.argv)) + u"\n")

            for k, v in self._metadata.items():
                fout.write(u"{}: {}\n".format(self._unicodize(k), self._unicodize(v)))

        os.chmod(self.get_file_path(self.METADATA_FILE_PATH), self.default_rights)
        log.info("metadata have been saved to " + self.get_file_path(self.METADATA_FILE_PATH))
        log.info("experiment folder: {}".format(self.get_experiment_dir()))
        if self._exit_code == 0 and self._exception is None:
            open(self.get_file_path(self.SUCCESS_PATH), "w").close()
        else:
            open(self.get_file_path(self.FAIL_PATH), "w").close()
            with open(self.get_file_path(self.FAIL_PATH), "w") as fout:
                print("exit code", self._exit_code, file=fout)
                if self._exception is not None:
                    print(self._exception, file=fout)

            if self._exception is not None:
                log.error(
                    "",
                    exc_info=(self._exc_type, self._exception, self._traceback)
                )

    def get_experiment_dir(self):
        """
        Construct experiment's directory every time in case setup is run many times.

        :return: exp dir
        """
        if self._expdir is None:
            exp_dir_name = "".join((self._name, self._date_str))
            self._expdir = os.path.join(self._root_dir, exp_dir_name)
        return self._expdir

    def _set_root_dir(self, root_dir):
        """Set directory of the experiments root.

        :param root_dir: Experiments root path
        :return: None
        """
        self._expdir = None
        self._root_dir = root_dir

    def _set_name(self, exp_name):
        """Set name of the experiment.

        :param exp_name: Name of the experiment
        :return: None
        """
        self._name = exp_name

    def get_file_path(self, file_name):
        """Get path to the file with given file_name.

        :param file_name: Name of the file (just name and extension)
        :return: Path to the file
        """
        if self.disabled:
            return os.devnull

        abs_path = os.path.join(self.get_experiment_dir(), file_name)
        # if the `file_name` contains "/" check if the dirs exist and create them otherwise
        if "/" in file_name:
            folder, _ = abs_path.rsplit("/", 1)
            if not os.path.isdir(folder):
                os.makedirs(folder)

        return abs_path

    def backup_files(self, files_list):
        """Backup files in the given list to the experiment folder.

        :param files_list: List of files
        :return: None
        """
        if self.disabled:
            return

        for file_path in files_list:
            if "/" in file_path:
                filename = file_path[file_path.rfind("/") + 1:]  # take only the file name
            else:
                filename = file_path

            if os.path.exists(self.get_file_path(filename)):
                log.warning("{} already exists! Skipping backup".format(self.get_file_path(filename)))
                continue

            copyfile(file_path, self.get_file_path(filename))
            copystat(file_path, self.get_file_path(filename))
            os.chmod(self.get_file_path(filename), self.default_rights)

        log.info("following files have been saved to experiment folder: {}".format(
            ", ".join(files_list)))

    def backup_sources(self, paths, output="sources.zip"):
        zf = zipfile.ZipFile(self.get_file_path(output), "w")
        for path in paths:
            for dirname, subdirs, files in os.walk(path):
                zf.write(dirname)
                for filename in files:
                    zf.write(os.path.join(dirname, filename))

        # Create __main__.py to replicate the experiment
        if not os.path.exists("__main__.py"):
            with io.open("__main__.py", "w", encoding="utf-8") as fout:
                fout.write(u"#!/usr/bin/env python\n")
                fout.write(u"# -*- coding: utf-8 -*-\n")
                fout.write(u"import subprocess\n")
                fout.write(
                    u"print(subprocess.check_output(['" + u"','".join(map(self._unicodize, sys.argv)) + u"']))\n\n")
            zf.write("__main__.py")
            try:
                os.remove("__main__.py")
            except:
                pass
        zf.close()

    def set_metadata(self, key, value):
        """Add metadata to the experiment. Will be used for the final export.

        :param key: Key of metadata
        :param value: Value of metadata
        :return: None
        """
        self._metadata[key] = value


def clean_experiment_dir(override_dir):
    """
    Cleans experiment folder.
    :param bool override_dir: If true, clean the folder, if false, check it's empty or doesn't exists
    :return:
    """
    experiment_dir = get_file_path("")
    # Check experiment_dir is empty or doesn't exists
    if not override_dir:
        if not os.path.exists(experiment_dir) or not os.listdir(experiment_dir):
            return
        else:
            raise FileExistsError(
                "Directory '{}' already exists and is not empty! "
                "Use override_dir=True to clean the directory."
                    .format(name())
            )
    else:
        # Dir doesn't exists, so everything's fine.
        if not os.path.exists(experiment_dir):
            return
        # Remove all files in the directory
        for the_file in os.listdir(experiment_dir):
            file_path = os.path.join(experiment_dir, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def setup(root_dir, exp_name=None, with_date=False, backup=True, default_rights=RWXRWS, loglevel=logging.DEBUG,
          log_filename='log.txt', disable_stderr=False, override_dir=False):
    """Set up Experiment handler.

    :param root_dir: Path to experiments root directory. New directories will be created in the folder.
    :param exp_name: Name of the parameter, will be used for new folder creation.
    :param with_date: True, if you want to include datetime in the experiment's dir name
    :param backup: Backup the entry-script into the experiment folder
    :param default_rights: Default rights for files in experiment
    :param loglevel: Loglevel, DEBUG by default, can be overriden by FLEXP_LOGLEVEL environment variable.
    :param log_filename: Filename of log in experiment dir. 'log.txt' by default. If None, logging to file is disabled.
    :param disable_stderr: Enable/disable logging on stderr. False by default.
    :param bool override_dir: If True, remove all contents of the directory.
                              If False and there is any file in the directory, raise an exception.
    """
    if "experiment" in _eh:
        raise Exception("flexp.setup() called twice. Use flexp.close() before calling again.")
    _eh["experiment"] = ExperimentHandler(default_rights=default_rights)
    _eh["experiment"].setup(root_dir, exp_name, with_date=with_date)

    # Clean the directory or check it's empty
    clean_experiment_dir(override_dir)

    if backup:
        _eh["experiment"].backup_files([sys.argv[0]])
    atexit.register(_eh["experiment"]._write_metadata)
    if log_filename is not None:
        log_filename = get_file_path(log_filename)
    _setup_logging(loglevel, log_filename, disable_stderr)


def describe(description):
    """Preserve description of this experiment."""
    if "experiment" not in _eh:
        raise ValueError("Call flexp.setup first! flexp.describe after that")
    with open(_eh["experiment"].get_file_path("description.txt"), "wt") as fx:
        print(description, file=fx)


def name():
    """Return the name of current experiment."""
    return _eh["experiment"]._name


def static(label, folder):
    """Setup a static directory = containing data across experiments (e.g. cache, models).

    Example usage:
    >>> flexp.static("data", "/www/data/mydatadir")
    >>> flexp.get_static_file("data", "corpus.txt")
    """
    root_dir, folder = os.path.abspath(folder).rsplit("/", 1)
    if label not in _eh:
        _eh[label] = ExperimentHandler()
    _eh[label].setup(root_dir, folder, False)


def backup_files(files_list):
    """Backup files in the given list to the experiment folder.

    :param files_list: List of files
    """
    _eh["experiment"].backup_files(files_list)


def backup_sources(paths, output_name="sources.zip"):
    """Backup given directory to the experiment folder.

    :param paths: list[str] Path to directories to backup
    :param str output_name: Name of the zipped file.
    """
    _eh["experiment"].backup_sources(paths, output_name)


def get_static_file(folder, file_name):
    """Get path to a file inside some static folder (such as cache, data etc.)."""
    if folder not in _eh:
        raise KeyError(
            "No static \"{}\". Didn't you swap 'name' and 'path' during init \"static(name, path)\"?".format(folder))
    return _eh[folder].get_file_path(file_name)


# shorter alias
static_file = get_static_file


def get_file_path(file_name):
    """Get path to the file with given file_name.

    :param file_name: Name of the file (just name and extension)
    :return: {str} Path to the file
    """
    return _eh["experiment"].get_file_path(file_name)


# shorter alias
get_file = get_file_path


def set_metadata(key, value):
    """Add metadata to the experiment. Will be used for the final export.

    :param key: Key of metadata
    :param value: Value of metadata
    :return: None
    """
    _eh["experiment"].set_metadata(key, value)


def disable():
    """Surpress all output and returns /dev/null as path to all files."""
    _eh["experiment"].disabled = True
    _setup_logging(logging.FATAL, None, True)


def close():
    """
    Writes experiment metadata and stops logging.
    Allows to call setup() twice.
    """
    _eh["experiment"]._write_metadata()
    _close_file_handlers()
    del _eh["experiment"]
