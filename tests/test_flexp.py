# coding: utf-8

import atexit
import io
import os
from os import path
import shutil

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
