#!/usr/bin/env python

import io
import os.path
import sys

from setuptools import setup, find_packages


def _open(fname):
    """Read a file relatively to this setup.py."""
    return io.open(os.path.join(os.path.dirname(__file__), fname), "rt",
                   encoding="utf-8")


requirements = [line.rstrip('\n') for line in _open('requirements.txt')]

PY2 = sys.version_info[0] == 2

if PY2:
    packages = find_packages()
    # separate entry_points as well?
else:
    packages = [
        "flexp",
        "flexp.flexp",
        "flexp.flow",
        "flexp.browser",
        "flexp.browser.html",
    ]

setup(
    name="flexp",
    version="1.0",
    url="https://github.com/seznam/flexp/",
    author="Seznam.cz research team",
    author_email="research@firma.seznam.cz",
    description="Toolkit for reproducibility of scientific experiments"
                " bundled together with flow-oriented programming paradigm.",
    long_description=_open('README.md').read(),
    packages=packages,
    package_data={
        'flow.flexp': ["static/images/*", "static/*.png", "static/*.css", "static/*.js", "static/*.ico"],
    },
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'flexp-browser = flexp.browser:main',
        ]
    },
    test_suite='nose.collector',
    tests_require=['nose', 'testfixtures'],
)
