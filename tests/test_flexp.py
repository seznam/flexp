# coding: utf-8

import atexit
import io
import os
import time
from os import path
import shutil
from pprint import pprint

import pytest

from flexp import flexp


def test_working():
    flexp.setup("tests/data/", "exp01", False)

    expdir = path.join("tests/data/", "exp01")
    assert path.isdir(expdir), "flexp didn't create experiment dir"

    with io.open("tests/testfile.txt", "wt") as x:
        x.write(u"hello")

    flexp.backup_files(["tests/testfile.txt"])
    assert path.exists(path.join("tests/data/", "exp01", "testfile.txt"))

    # forbid flexp creating metadata on exit
    if hasattr(atexit, "unregister"):
        getattr(atexit, "unregister")(flexp.core._eh["experiment"]._write_metadata)

    os.unlink("tests/testfile.txt")
    os.unlink(path.join(expdir, "testfile.txt"))
    if not hasattr(atexit, "unregister") and path.exists(
            path.join(expdir, "flexp_info.txt")):
        os.unlink(path.join(expdir, "flexp_info.txt"))
    flexp.disable()
    shutil.rmtree(expdir)


def test_static():
    flexp.static("data", "tests/mydatafolder")
    assert path.isdir(
        "tests/mydatafolder"), "flexp didn't create static root directory"

    file_path = flexp.get_static_file("data", "nonexisting/file.txt")

    static_folder = "tests/mydatafolder/nonexisting"
    assert path.isdir(static_folder), "flexp didn't create static subdirectory"

    with io.open(file_path, "wt") as x:
        x.write(u"hello")

    os.unlink(file_path)
    os.rmdir(static_folder)


def test_close():
    exp_root_dir = "tests/data/"
    expdir1 = path.join(exp_root_dir, "exp01")
    expdir2 = path.join(exp_root_dir, "exp02")

    # Remove the experiment dir if it exists
    if os.path.exists(expdir1):
        shutil.rmtree(expdir1)
    if os.path.exists(expdir2):
        shutil.rmtree(expdir2)

    # We have to reset the _eh to make flexp stop complaining about calling setup twice.
    flexp.core._eh = {}
    flexp.setup(exp_root_dir, "exp01", with_date=False)
    flexp.close()

    assert path.isfile(os.path.join(expdir1, "flexp_info.txt")), \
        "flexp didn't create flexp_info.txt after calling flexp.close()"

    flexp.setup(exp_root_dir, "exp02", with_date=False)
    flexp.close()

    # Ensure log files doesn't contain the same rows
    log1 = load_log_without_timestamp(os.path.join(expdir1, "log.txt"))
    log2 = load_log_without_timestamp(os.path.join(expdir2, "log.txt"))
    assert len(set(log1) & set(log2)) == 0, \
        "Log files contains same rows"

    # Ensure not possible to call flexp.setup() twice
    with pytest.raises(Exception):
        flexp.setup(exp_root_dir, "exp01", with_date=False, override_dir=True)
        flexp.setup(exp_root_dir, "exp02", with_date=False, override_dir=True)

    # Disable logging to be able to delete the experiment directory.
    flexp.disable()

    # Remove the experiment dir
    if os.path.exists(expdir1):
        shutil.rmtree(expdir1)

    if os.path.exists(expdir2):
        shutil.rmtree(expdir2)


def load_log_without_timestamp(filename):
    with open(filename) as f:
        return [row[25:] for row in f.readlines()]
