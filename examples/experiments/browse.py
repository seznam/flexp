"""
This will run flexp_browser with 8 sections in menu: "Flexp info", "CSV files", "Experiment info, description",
"Histograms", "Confusion matrices", etc.
"""
import click
import logging

from flexp.browser import browser
from flexp.browser.html.generic import (
    CsvToHtml, ImagesToHtml,
    TxtToHtml, FilesToHtml, FlexpInfoToHtml)
from flexp.browser.utils import setup_logging


log = logging.getLogger(__name__)

setup_logging("info")


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
        TxtToHtml(),
        FilesToHtml(),
    ]
    browser.run(port=port, chain=chain)


if __name__ == "__main__":
    main()
