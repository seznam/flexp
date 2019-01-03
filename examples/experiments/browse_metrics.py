"""
This will run flexp_browser with 8 sections in menu: "Flexp info", "CSV files", "Experiment info, description",
"Histograms", "Confusion matrices", etc.
"""
import sys

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
    """
    Returns row from metrics.csv with the lowest `RMSE dev` value
    Example metrics.csv:
    method;RMSE dev;RMSE train
    method1;0.35;0.27
    method2;0.30;0.24

    Returns:
    [
        {"method", "method_2", "RMSE dev": 0.30, "RMSE train": 0.24},
    ]

    :param str file_path: Path to a file with metrics
    :return list[dict[str, Any]]:
    """
    reader = CsvToHtml().iterate_csv(file_path)
    metric_names = next(reader)

    metric_name = "RMSE dev"
    min_value = float("inf")

    metrics_row_to_return = None
    for metric_values in reader:
        metrics_dict = dict(zip(metric_names, metric_values))
        value = float(metrics_dict.get(metric_name, min_value))
        if value <= min_value:
            metrics_row_to_return = metrics_dict
            min_value = value

    return [metrics_row_to_return]


@click.command()
@click.option('--port', '-p', default=7777, help='Port')
def main(port):
    browser.run(port=port, get_metrics_fcn=get_metrics, metrics_file="metrics.csv")


if __name__ == "__main__":
    main()
