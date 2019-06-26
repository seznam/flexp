#!/usr/bin/env python
# coding: utf8
import sys

from examples.example_custom_pages.features_handler import FeaturesHandler

import click
import logging

from flexp.browser import browser
from flexp.browser.utils import setup_logging
from flexp.browser.html.generic import CsvToHtml
import os
from flexp.flow import Chain


log = logging.getLogger(__name__)

setup_logging("debug")
py_version = sys.version_info[0]


@click.command()
@click.option('--port', '-p', default=8111, help='Port')
def main(port):
    chain = [
        CsvToHtml(file_name_pattern="worst_examples_.*.csv", title="Worst examples", delimiter='\t'),
    ]

    add_paths = [(r"/features/", FeaturesHandler, {"experiments_folder": os.getcwd(), "html_chain": Chain(chain)})]

    browser.run(port=port, chain=chain, additional_paths=add_paths)


if __name__ == "__main__":
    main()

