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


def get_metrics(file_path):
    reader = CsvToHtml().iterate_csv(file_path)

    metric_col = 1
    metric_name = next(reader)[metric_col]
    metric_val = min([row[metric_col] for row in reader])

    return {metric_name: metric_val}


@click.command()
@click.option('--port', '-p', default=7777, help='Port')
def main(port):
    browser.run(port=port, get_metrics_fcn=get_metrics, metrics_filename="other_metrics.csv")


if __name__ == "__main__":
    main()
