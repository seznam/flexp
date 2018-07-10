import click

from flexp.browser import browser
from flexp.browser.html.generic import (
    CsvToHtml, ImagesToHtml,
    FlexpInfoToHtml, TxtToHtml)
from flexp.browser.html.to_html import ToHtml
from flexp.browser.utils import setup_logging
from flexp.utils import get_logger


log = get_logger(__name__)


setup_logging("info")


# TODO Copy this class to your desired file------------
# TODO Change class name ------------------------------
class ExampleToHtml(ToHtml):
    # TODO Change comment -----------------------------
    """Example module that demonstrates how to make own module to flexp browser."""

    def __init__(self, file_name_pattern=None):
        # (optional) TODO set default file_name_patter which is a regex matching filenames
        super(ExampleToHtml, self).__init__(file_name_pattern)

    # TODO Implement to_html method which is called per-file OR implement get_html -------
    def to_html(self, file_path):
        """Return HTML code to be shown.

        W3.CSS styling can be used:   http://www.w3schools.com/w3css/default.asp
        Variables self.experiment_path and self.experiment_folder can be used
        :return: string HTML code
        """
        # TODO Change HTML content  -------------------
        with open(file_path) as f:
            return "<div>Content of file {}<br/>{}</div>".format(file_path, f.read())

    # TODO if you have implemented to_html delete this whole method --------
    def get_html(self):
        """Return HTML code to be shown.

        W3.CSS styling can be used:   http://www.w3schools.com/w3css/default.asp
        Variables self.experiment_path and self.experiment_folder can be used
        :return: string HTML code
        """
        # TODO Change HTML content  -------------------
        file_names = self.get_files()  # Return 0th file from the experiment folder
        return """
            modules/example_to_html.py<br/>
            Experiment name is <span class='w3-tag w3-green'>{folder}</span>
            and contents a file <span class='w3-tag w3-yellow'>{filename}</span>""".format(
            folder=self.experiment_folder, filename=file_names)

    def show_file(self, file_path_exp):
        """Used to filter out files returned by get_files().

        :param file_path_exp: string File path from experiment folder
        :return: bool
        """
        return True


@click.command()
@click.option('--port', '-p', default=7777, help='Port')
def main(port):
    chain = [
        FlexpInfoToHtml(),
        CsvToHtml(),
        TxtToHtml(file_name_pattern="(description.txt)", title="Experiment info, description"),
        ImagesToHtml(file_name_pattern="^hist", title="Histograms"),
        ImagesToHtml(file_name_pattern="^confusion_matrix", title="Confusion matrices"),
        ImagesToHtml(file_name_pattern="^(?!.*(roc|confusion_matrix)).*", title="Other images"),

        # your custom module
        ExampleToHtml()
    ]
    browser.run(port=port, chain=chain)


if __name__ == "__main__":
    main()
