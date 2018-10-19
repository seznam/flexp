# coding: utf-8

import atexit
import io
import os
from os import path
import shutil

import pytest

from flexp import flexp


def test_override():
    expdir = path.join("tests/data/", "exp01")

    # Remove the experiment dir if it exists
    if os.path.exists(expdir):
        shutil.rmtree(expdir)

    # We have to reset the _eh to make flexp stop complaining about calling setup twice.
    flexp.core._eh = {}
    flexp.setup("tests/data/", "exp01", False, override_dir=False)

    assert path.isdir(expdir), "flexp didn't create experiment dir with override_dir=False"

    # Test that it fails to create the directory, there should be logging file already.
    with pytest.raises(FileExistsError):
        flexp.core._eh = {}
        flexp.setup("tests/data/", "exp01", False, override_dir=False)

    # This should be ok
    flexp.core._eh = {}
    flexp.setup("tests/data/", "exp01", False, override_dir=True)

    # Disable logging to be able to delete the experiment directory.
    flexp.disable()

    # Remove the experiment dir
    if os.path.exists(expdir):
        shutil.rmtree(expdir)
