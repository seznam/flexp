#!/usr/bin/env python
# coding: utf8
import csv
import io

import sys

from examples.example_custom_pages.features_handler import FeaturesHandler
from flexp.browser.html.to_html import ToHtml

import click
import logging

from flexp.browser import browser
from flexp.browser.utils import setup_logging
from os.path import join, split
from flexp.browser.html.generic import CsvToHtml
import os
from flexp.flow import Chain


log = logging.getLogger(__name__)

setup_logging("debug")
py_version = sys.version_info[0]


# custom function to be called in flexp/browser/browser.py
def annotation_save(value, ajax_handler):
    key = ajax_handler.get_argument('id')
    annotation_file = ajax_handler.get_argument('annotation_file')

    annotation_dict = {}
    with open(annotation_file, 'r') as annotations:
        for line in annotations.readlines():
            k, v = line.strip().split('\t')
            annotation_dict[k] = v
    annotation_dict[key] = value
    with open(annotation_file, 'w') as annotations_file:
        for key, value in annotation_dict.items():
            annotations_file.write("{}\t{}\n".format(key, value))


# add custom function to browser.actions list
browser.actions['annotation_save'] = annotation_save

# create this folder for static files
STATIC_PATH = 'static_annotations'


# edit this depends on your necessities
# todo maybe add generic version of this to build-in modules
class CsvToHtmlEditable(ToHtml):

    ANNOTATION_FILE = "annotation_file.txt"

    def __init__(self, file_name_pattern=None, title="CSV files", max_rows=100, max_files=None, delimiter=str(";"),
                 quotechar=str("\""), key=(0, ), url_columns=None, classes_names=None):
        super(CsvToHtmlEditable, self).__init__(file_name_pattern, title)
        self.max_rows = max_rows
        self.max_files = max_files
        self.delimiter = delimiter
        self.quotechar = quotechar

        self.key = key
        self.url_columns = url_columns if url_columns else []
        self.classes_names = classes_names if classes_names else {}

    def get_html(self):
        out = '<style type="text/css" scoped>table.auto {width: 100%; table-layout: auto;}</style>' \
              '<script src="/'+STATIC_PATH+'/annotate_script.js"></script>'
        for csv_file in self.get_files()[:self.max_files]:
            out += self.csv_to_html(join(self.experiment_path, csv_file))
        return out

    def show_file(self, file_path_exp):
        return file_path_exp[-3:] in ("csv", "tsv")

    def csv_to_html(self, csv_file):
        html = ""
        # Open the CSV file for reading
        mode = "rb" if py_version == 2 else "r"
        with io.open(csv_file, mode) as csvfile:
            if self.delimiter is None or self.quotechar is None:
                try:
                    dialect = csv.Sniffer().sniff(csvfile.read(2048))
                    csvfile.seek(0)
                except Exception as e:
                    log.error("{} has exception {!s}".format(csv_file, e))
                    return ""
                reader = csv.reader(csvfile, dialect)
            else:
                reader = csv.reader(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)

            # initialize rownum variable
            rownum = 0

            html += "<table class='auto w3-table w3-bordered w3-border w3-hoverable w3-card-2 tablesorter'>\n"
            folder, filename = split(csv_file)
            href = join("file/", self.experiment_folder, filename)
            html += "<caption><a href='%s'>%s</a></caption>" % (href, filename)

            # generate table contents
            for row in reader:  # Read a single row from the CSV file
                if py_version == 2:
                    row = [item.decode("utf8") for item in row]
                # write header row. assumes first row in csv contains header
                if rownum == 0:
                    html += "<thead>"
                    html += "<tr class='w3-green'>"  # write <tr> tag
                    for column in row:
                        html += '<th>' + column + '</th>'
                    html += '<th>' + "Reference" + '</th>'
                    html += '</tr>\n'
                    html += "</thead>"

                # write all other rows
                else:
                    html += '<tr id="tr" bgcolor="#ffffff">'
                    for i_r, column in enumerate(row):
                        html += '<td>' + column + '</td>'
                    html += "<td><a href='features/?id={}'>Ref</a></td>".format(row[0])
                    html += '</tr>\n'

                # increment row count
                rownum += 1
                if self.max_rows is not None and rownum >= self.max_rows:
                    html += "<tr><td colspan='{}'><center><i>following rows hidden</i></center></td></tr>\n"\
                        .format(len(row))
                    break

            html += '</table>\n'
        return html

    def to_html(self, file_name):
        pass


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

