from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import csv
import io
import os
import random
import re
import sys
import html as html_module
from datetime import datetime
from itertools import islice
from os import path
from os.path import join, split

from flexp.browser.html.to_html import ToHtml
from flexp.browser.utils import get_link_to_file
from flexp.utils import get_logger


log = get_logger(__name__)

py_version = sys.version_info[0]


class TxtToHtml(ToHtml):
    """Print file content"""

    def __init__(self, file_name_pattern=".*\.txt", title="Text files", editable=True, keep_html=False, trim_at=100):
        """

        :param file_name_pattern:
        :param title:
        :param editable:
        :param keep_html:
        :param trim_at: Show max. of trim_at lines. (0 to disable trimming)
        """
        super(TxtToHtml, self).__init__(file_name_pattern, title=title)
        self.keep_html = keep_html
        self.editable = editable
        self.trim_at = trim_at

    def get_pattern(self):
        return "<div class='txt2html'>" \
               "<div>" \
               "<b>{file_link}</b> " \
               "<div class=\"edit padding-right {class_editable}\" " \
               "onclick=\"$('#new_content').text('{content_strip}'); " \
               "$('#edit-txt').data('folder', '{experiment_path}').data('file_name', '{filename}').dialog('open')\">&nbsp;" \
               "</div>" \
               "</div>" \
               "<p>{content}</p>" \
               "{trim_msg}" \
               "</div>"

    def to_html(self, file_name):
        filepath = join(self.experiment_folder, file_name)
        with io.open(filepath, encoding="utf8") as f:
            lines = list(islice(f, self.trim_at + 1))
            trimmed = len(lines) > self.trim_at
            if trimmed:
                lines = lines[:self.trim_at]
            trim_msg = '<i>(file trimmed at {} lines)</i>'.format(self.trim_at) if trimmed else ''
            raw_content = ''.join(lines)

        content = raw_content
        if not self.keep_html:
            content = raw_content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>\n")\
                .replace("  ", "&nbsp;&nbsp;")

        raw_content = raw_content.replace("\n", "\\n").replace('"', '\\"').replace("'", "\\'")
        raw_content = html_module.escape(raw_content)

        class_editable = "" if self.editable and not trimmed else "hide"

        href = join("file/", self.experiment_folder, file_name)
        path_to_file = join(self.experiment_path, file_name)
        link = get_link_to_file(file_name, href, path_to_file=path_to_file)

        return self.get_pattern().format(
            content=content,
            filename=file_name,
            file_link=link,
            content_strip=raw_content,
            experiment_path=self.experiment_path,
            class_editable=class_editable,
            trim_msg=trim_msg,
            )


class FlexpInfoToHtml(TxtToHtml):
    """Print content of flexp_info.txt with link to experiment log"""

    def __init__(self, file_name_pattern="flexp_info.txt", title="Flexp info", editable=False, log_file_name="log.txt"):
        super(FlexpInfoToHtml, self).__init__(file_name_pattern, title, editable=editable)
        self.log_file_name = log_file_name

    def get_html(self):
        out = super(FlexpInfoToHtml, self).get_html()
        log_file_path = os.path.join(self.experiment_path, self.log_file_name)
        if self.log_file_name and os.path.exists(log_file_path):
            href = join("file/", self.experiment_folder, self.log_file_name)
            out += get_link_to_file(self.log_file_name, href)
        return out


class DescriptionToHtml(ToHtml):
    """Retrieve an description from 'description.txt'."""

    DESCRIPTION_FILE = "description.txt"

    def __init__(self, file_name_pattern=None, title="Description"):
        super(DescriptionToHtml, self).__init__(file_name_pattern, title)

    @staticmethod
    def get_description_html(basedir, replace_newlines=True):
        filepath = join(basedir, DescriptionToHtml.DESCRIPTION_FILE)

        if not path.exists(filepath):
            return "{} not found".format(DescriptionToHtml.DESCRIPTION_FILE)

        with open(filepath) as f:
            s = f.read().replace("<", "&lt;").replace(">", "&gt;")
            if replace_newlines:
                s = s.replace("\n", "<br/>\n")
            return s

    def get_html(self):
        return DescriptionToHtml.get_description_html(self.experiment_path)

    def to_html(self, file_name):
        pass


class TimeToHtml(ToHtml):
    """Show the duration of an experiment from log.txt."""

    def __init__(self, title="Time"):
        self.time_re = re.compile(r'(\d{2,4})[\-\.]?(\d{1,2})[\-\.]?(\d{1,2})[ T\-_]?(\d{1,2})[\:\.](\d{1,2})[\:\.](\d{1,2})')
        super(TimeToHtml, self).__init__("log.txt", title)

    def to_html(self, file_name):
        # jump_back = -2048
        filename = join(self.experiment_path, file_name)
        with open(filename, "rb") as f:
            first_line = next(iter(f)).decode("utf8")
            start_time = self.time_re.search(first_line)
            end_time = None

            if start_time is None:
                return ""

            # try:
            #     f.seek(jump_back, 2)
            # except:
            #     return ""

            for line in reversed(f.readlines()):
                end_time = self.time_re.search(line.decode("utf8"))
                if end_time is not None:
                    break
            if end_time is None:
                log.error("Could not find end time - increase jump back")
                return ""

            try:
                start_time = datetime(*[int(x) for x in start_time.groups()])
                end_time = datetime(*[int(x) for x in end_time.groups()])
            except:
                log.error("Parsing '{}' or '{}' failed".format(start_time, end_time))
                return ""

            duration = end_time - start_time
            hours = duration.seconds // (60 * 60)
            minutes = duration.seconds % (60 * 60) // 60
            seconds = duration.seconds % (60 * 60)

            return u"start: {:%Y-%m-%d %X}  --- duration: {:d}d, {:d}:{:d}:{:d} ----> end: {:%Y-%m-%d %X}".format(
                start_time,
                duration.days, hours, minutes, seconds,
                end_time)


class CsvToHtml(ToHtml):
    """
    Print csv files to html
    """

    def __init__(self, file_name_pattern=None, title="CSV files", max_rows=100, max_files=None, delimiter=str(";"),
                 quotechar=str("\"")):
        super(CsvToHtml, self).__init__(file_name_pattern, title)
        self.max_rows = max_rows
        self.max_files = max_files
        self.delimiter = delimiter
        self.quotechar = quotechar

    def get_html(self):
        out = ""
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

            # write <table> tag
            html += "<p><table class='w3-table w3-bordered w3-striped w3-border w3-hoverable w3-card-2 tablesorter'>\n"
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
                    html += '</tr>\n'
                    html += "</thead>"

                # write all other rows
                else:
                    html += '<tr>'
                    for column in row:
                        html += '<td>' + column + '</td>'
                    html += '</tr>\n'

                # increment row count
                rownum += 1
                if self.max_rows is not None and rownum >= self.max_rows:
                    html += "<tr><td colspan='{}'><center><i>following rows hidden</i></center></td></tr>\n"\
                        .format(len(row))
                    break

            # write </table> tag
            html += '</table></p>\n'
        return html

    def to_html(self, file_name):
        pass


class ImagesToHtml(ToHtml):
    """Create HTML representation of all images from experiment folder."""

    MAX_NR_IMAGES_TO_SHOW_LARGE = 10

    @staticmethod
    def is_image(filename):
        return os.path.isfile(filename) and os.path.splitext(filename)[1] in (".jpeg", ".jpg", ".png")

    def __init__(self, file_name_pattern=None, title="Images"):
        """Create <img> html tag for all images.

        :param file_name_pattern: string Returns only images whose name matches regexp patter
        """
        super(ImagesToHtml, self).__init__(file_name_pattern, title)

    def get_html(self):
        out = ""

        images = self.get_files()  # Get images
        pattern = "<div class='w3-card-2 image %(class_image)s'>" \
                  "<a href='%(href)s'><img src='%(src)s' title='%(title)s' alt='%(title)s' /></a>" \
                  "<div class='w3-container' ><p>%(description)s</p></div>" \
                  "</div>"
        class_image = "small-image" if len(images) > self.MAX_NR_IMAGES_TO_SHOW_LARGE else "large-image"
        html_list = []
        for img_name in images:
            href = join("file/", self.experiment_folder, img_name)
            html_list.append(pattern % {'href': href, 'title': img_name, 'src': href, 'description': img_name,
                                        'class_image': class_image})

        return out + "\n".join(html_list)

    def show_file(self, file_path_exp):
        """Return true if given filepath is an image file.

        :return: bool
        """
        return ImagesToHtml.is_image(join(self.experiment_path, file_path_exp))

    def to_html(self, file_name):
        pass


class StringToHtml(ToHtml):
    """ Prints string given in constructor. """

    def __init__(self, message, file_name_pattern=None, title="Message", default_collapsed=False):
        self.message = message
        self.default_collapsed = default_collapsed
        super(StringToHtml, self).__init__(file_name_pattern, title=title)

    def get_html(self):
        return self.message

    def to_html(self, file_name):
        pass


class FilesToHtml(ToHtml):
    """ Print list of files """

    def __init__(self, file_name_pattern=".*", title="All files", show_images=False):
        super(FilesToHtml, self).__init__(file_name_pattern, title)
        self.show_images = show_images

    def get_pattern(self):
        return "<li>%(link)s</li>"

    def get_html(self):
        out = ""
        html_list = []
        for filename in self.get_files():
            html_list.append(self.to_html(filename))
        out += "<ul class='w3-ul w3-card-2 w3-hoverable'>" + "\n".join(html_list) + "</ul>"
        return out

    def to_html(self, file_name):
        href = join("file/", self.experiment_folder, file_name)
        path_to_file = join(self.experiment_path, file_name)
        link = get_link_to_file(file_name, href, path_to_file=path_to_file)
        return self.get_pattern() % {"link": link}
