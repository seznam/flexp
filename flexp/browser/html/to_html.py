from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from os import listdir
from os.path import join, isdir
import re

from flexp.browser.utils import message
from flexp.utils import get_logger, natural_sort, id_generator


log = get_logger(__name__)


class ToHtml(object):
    """Abstract class to print something to html."""

    def __init__(self, file_name_pattern=None, title=None):
        self.experiment_path = None
        self.experiment_folder = None
        self.file_name_pattern = file_name_pattern
        self.title = title or self.__class__.__name__
        self.id = id_generator()

    def process(self, data):
        """Append new HTML content to data["html"]."""
        # Save data
        self.experiment_path = data["experiment_path"]
        self.experiment_folder = data["experiment_folder"]

        try:
            content = self.get_html()
        except Exception as e:
            content = message(str(e))

        # Initialization
        data.setdefault("html", []).append("""
            <div class='toggle-{id}-all'>
            <h2 id='{title}'>{title}</h2>
            <div class='toggle-{id}-content'>
                {content}
            </div>
            <hr />
            </div>""".format(title=self.title, class_name=self.__class__.__name__,
                             content=content, id=self.id))

        # Process headers and scripts - allows modules to manipulate HEAD and
        # add various scripts at the end of BODY.
        self.process_header(data)
        self.process_scripts(data)

    def get_files(self, subfolder=""):
        """Recursively retrieves all files that satisfies function show_file().

        :param subfolder: string Relative path from experiment_folder
        :return: list of file paths (from experiment folder)
        """
        files_to_return = []
        for file_name in natural_sort(listdir(join(self.experiment_path, subfolder))):
            file_path_exp = join(subfolder, file_name)
            if isdir(join(self.experiment_path, file_path_exp)):
                files_to_return += self.get_files(file_path_exp)
            else:
                if (self.file_name_pattern is None or re.search(self.file_name_pattern, file_path_exp)) \
                        and (self.show_file(file_path_exp)):
                    files_to_return.append(file_path_exp)
        return files_to_return

    def show_file(self, file_path_exp):
        """Return true if the `file_path_exp` should be processed by this module.

        :param file_path_exp: {string} file path from experiment folder
        :return: bool
        """
        return True

    def get_html(self):
        """Method free to overwrite - has access to all files at once.

        By default it iterates over allowed files and pass them to `self.to_html` method.

        :return: {str} HTML content of the module
        """
        content = []
        for file_name in self.get_files():
            try:
                file_content = self.to_html(file_name)
            except Exception as e:
                file_content = message(str(e))

            content.append(file_content)

        return u"\n".join(content)

    def process_scripts(self, data):
        """
        Allows modules to access SCRIPTS section in the generated HTML and
        modify it. The scripts are supposed to be stored in "scripts" key of
         data as data["scripts"]["namespace"] = list().

        Example:
        data["scripts"]["bokeh"]

        :param data: standard data dict
        :return:
        """
        pass

    def process_header(self, data):
        """
        Allows modules to access HEADER section in the generated HTML and
        modify it. The headers are supposed to be stored in "header" key of
         data as data["header"]["namespace"] = list().

        :param data: standard data dict
        :return:
        """
        pass

    def to_html(self, file_name):
        """Transform content of file under `file_name` into HTML string and return it."""
        raise NotImplementedError("Implement either to_html or overwrite get_html")
