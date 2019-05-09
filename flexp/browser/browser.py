"""Flexp browser is a HTTP server for easier browsing of results of many experiments.

Usage:
  flexp-browser --p <port>
  flexp-browser (-h | --help)

Options:
  -h --help     Show this screen.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import os.path as path
import re
import shutil
import sys
import traceback

import click
import tornado.ioloop
import tornado.web
from flexp.browser.utils import setup_logging

from flexp.browser.html.generic import DescriptionToHtml, FilesToHtml, ImagesToHtml, FlexpInfoToHtml, CsvToHtml, \
    TxtToHtml, StringToHtml
from flexp.browser.html.to_html import ToHtml
from flexp.flow import Chain
from flexp.utils import get_logger
from flexp.utils import import_by_filename, PartialFormatter, exception_safe

log = get_logger(__name__)

default_html_chain = (
    FlexpInfoToHtml(),
    CsvToHtml(file_name_pattern="metrics.csv", title="Main metrics"),
    ImagesToHtml(),
    CsvToHtml(file_name_pattern="^(?!.*(metrics.csv)).*"),
    TxtToHtml(),
    FilesToHtml(),
)


def default_get_metrics(file_path):
    """
    Example metrics.csv:
    method,metric 1, metric 2
    method_1,0.1,0.2
    method_2,0.2,0.3

    Returns:
    [
        {"method", "method_1", "metric 1": 0.1, "metric 2": 0.2},
        {"method", "method_2", "metric 1": 0.2, "metric 2": 0.3},
    ]

    :param str file_path: Path to a file with metrics
    :return list[dict[str, Any]]:
    """
    reader = CsvToHtml().iterate_csv(file_path)
    metric_names = next(reader)

    metrics_list = []
    for metric_values in reader:
        metrics_dict = dict(zip(metric_names, metric_values))
        metrics_list.append(metrics_dict)

    return metrics_list


def run(
        port=7777,
        chain=default_html_chain,
        get_metrics_fcn=default_get_metrics,
        metrics_file="metrics.csv",
        experiments_dir=os.getcwd(),
):
    """
    Run the whole browser with optional own `port` number and `chain` of ToHtml modules.
    Allows reading main metrics from all experiments and show them in experiment list.
    :param int port: Port on which to start flexp browser
    :param list[ToHtml]|ToHtml chain: List of ToHtml instances that defines what to print
    :param (Callable[str]) -> list[dict[str, Any]] get_metrics_fcn: Function that takes filename of a file with
    metrics and return dict[metric_name, value].
    :param str metrics_file: Filename in each experiment dir which contains metrics values.
    :param str experiments_dir: Path to directory with experiments, default=<current_directory>
    """

    # append new modules to the default chain
    if isinstance(chain, ToHtml):
        chain = [chain]

    # handle wrong return type and exceptions in get_metrics_fcn
    get_metrics_fcn = return_type_list_of_dicts(get_metrics_fcn, return_on_fail=[{}])
    get_metrics_fcn = exception_safe(get_metrics_fcn, return_on_exception=[{}])

    main_handler_params = {
        "get_metrics_fcn": get_metrics_fcn,
        "metrics_file": metrics_file,
        "experiments_folder": experiments_dir,
        "html_chain": Chain(chain),
    }

    here_path = os.path.dirname(os.path.abspath(__file__))

    app = tornado.web.Application(
        [
            (r"/", MainHandler, main_handler_params),
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": path.join(here_path, "static/")}),
            (r"/file/(.*)", NoCacheStaticHandler, {'path': experiments_dir}),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': path.join(here_path, "static")}),
            (r"/ajax", AjaxHandler, {"experiments_folder": experiments_dir})
        ],
        {"debug": True}
    )

    app.listen(port)
    log.info("Starting server on port {:d}".format(port))
    tornado.ioloop.IOLoop.current().start()


class MainHandler(tornado.web.RequestHandler):
    """Browser's logic is all here."""

    _template = """
        <!DOCTYPE HTML>
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
            <title>Flexp Browser</title>
            <link rel="stylesheet" type="text/css" href="/static/w3.css">
            <link rel="stylesheet" type="text/css" href="/static/jquery-ui.min.css">
            <link rel="stylesheet" type="text/css" href="/static/style.css">
            <link rel="icon" type="image/png" href="/static/favicon-32x32.png" sizes="32x32">
            <link rel="icon" type="image/png" href="/static/favicon-16x16.png" sizes="16x16">
            <script src="/static/jquery-2.2.3.min.js"></script>
            <script src="/static/jquery-ui.min.js"></script>
            <script src="/static/jquery.tablesorter.min.js"></script>
            <script src="/static/script.js"></script>
            <!-- HEADER GENERATED FROM CHAIN -- START -->
            {header}
            <!-- HEADER GENERATED FROM CHAIN -- END -->
        </head>

        <body>
            <nav id='sidenav' class='w3-sidenav w3-light-grey w3-card-4' onclick='nav_onresize()'>
                {navigation}
            </nav>

            <section id='main' class="w3-main">

                {title}

                {content}

            </section>

            <footer id='footer'>
                <p class='info'>Copyright (c) 2016, Seznam.cz, a.s. <br />
                Tomáš Přinda &lt;tomas.prinda@firma.seznam.cz&gt;</p>
            </footer>

            <div id="dialog-confirm" title="Delete?">
              <p>
                <span class="ui-icon ui-icon-alert" style="float:left; margin:12px 12px 20px 0;"></span>
                Delete the folder?
              </p>
            </div>
            <div id="dialog-rename" title="Rename">
                <form>
                      <label for="new_name">New folder name:</label>
                      <input type="text" name="new_name" id="new_name" value="" class="text ui-widget-content ui-corner-all" />
                </form>
            </div>
            <div id="edit-txt" title="Replace contents">
                <form>
                        <label for="new_content">New content:</label>
                        <textarea 
                            cols=50 
                            rows=10 
                            type="text" 
                            name="new_content" 
                            id="new_content" 
                            class="text ui-widget-content ui-corner-all"
                        >
                        </textarea>
                </form>
            </div>

            <!-- SCRIPTS GENERATED FROM CHAIN -- START -->
            {scripts}
            <!-- SCRIPTS GENERATED FROM CHAIN -- END -->
        </body>

        </html>
        """

    def initialize(self, get_metrics_fcn, metrics_file, experiments_folder, html_chain):
        self.get_metrics_fcn = get_metrics_fcn
        self.metrics_file = metrics_file
        self.experiments_folder = experiments_folder
        self.html_chain = html_chain

    def get(self):
        experiment_folder = self.get_argument("experiment", default="")
        log.info("experiment folder {}".format(self.experiments_folder))
        experiment_path = path.join(self.experiments_folder, experiment_folder)

        if not path.isdir(experiment_path):
            experiment_folder = ""

        navigation_html = html_navigation(self.experiments_folder,
                                          experiment_folder)
        header_html = ""
        scripts_html = ""

        if experiment_folder != "":
            data = {"experiment_path": experiment_path,
                    "experiment_folder": experiment_folder,
                    "html": [],
                    "header": dict(),
                    "scripts": dict()
                    }
            # Use custom chain, if present
            if os.path.exists(experiment_path + "/custom_flexp_chain.py"):
                try:
                    custom_flexp_chain = import_by_filename(
                        'custom_flexp_chain',
                        experiment_path + "/custom_flexp_chain.py")
                    html_chain = custom_flexp_chain.get_chain()
                    html_chain = Chain(html_chain)
                except:
                    html_chain = Chain([StringToHtml(
                        "<h2>Error processing custom chain. {}</h2>"
                            .format(
                            traceback.format_exc().replace("\n", "</br>")),
                        title="Error in custom chain")] + self.html_chain.modules)
                finally:
                    if "custom_flexp_chain" in sys.modules:
                        del sys.modules["custom_flexp_chain"]

            else:
                html_chain = self.html_chain
            html_chain.process(data)
            html_chain.close()

            title_html = "<h1>{}</h1>".format(experiment_folder)
            content_html = u"\n".join(data['html'])
            navigation_html = html_anchor_navigation(
                experiment_path, experiment_folder,
                html_chain) + navigation_html

            header_html = u"\n".join(u"\n".join(html_lines)
                                     for head_section, html_lines
                                     in data["header"].items())

            scripts_html = u"\n".join(u"\n".join(script_lines)
                                      for script_section, script_lines
                                      in data["scripts"].items())

        else:
            title_html = "<h1>Experiments</h1>"
            content_html = html_table(self.experiments_folder, self.get_metrics_fcn, self.metrics_file)

        html = self._template.format(
            title=title_html,
            navigation=navigation_html,
            content=content_html,
            header=header_html,
            scripts=scripts_html)
        self.write(html)


class AjaxHandler(tornado.web.RequestHandler):
    """
    Handler controls behaviour when delete folder or rename folder or change file content icons are used.
    """

    def __init__(self, application, request, **kwargs):
        super(AjaxHandler, self).__init__(application, request, **kwargs)

    def initialize(self, experiments_folder):
        self.experiments_folder = experiments_folder

    def post(self):
        action = self.get_argument('action')
        value = self.get_argument('value')

        if action == "delete_folder":
            if "/" not in value:
                folder = os.path.join(self.experiments_folder, value)
                shutil.rmtree(folder)

        if action == "rename_folder":
            new_name = self.get_argument('new_name')
            folder = os.path.join(self.experiments_folder, value)
            new_folder = os.path.join(self.experiments_folder, new_name)
            if os.path.exists(folder) and not os.path.exists(
                    new_folder) and "/" not in value and "/" not in new_name:
                os.rename(folder, new_folder)
            else:
                self.send_error(500,
                                reason="Rename folder not successful. Check old and new name.")

        if action == "change_file_content":
            new_content = self.get_argument('new_content')
            file_name = self.get_argument('file_name')
            with open(os.path.join(self.experiments_folder, value, file_name),
                      "w") as file:
                file.write(new_content)


def html_table(base_dir, get_metrics_fcn, metrics_file):
    """Construct a html table of all experiment folders with description.
    :param base_dir: parent folder in which to look for an experiment folders
    :param (Callable[str]) -> list[dict[str, Any]] get_metrics_fcn: Function that takes filename of a file with
    metrics and return dict[metric_name, value].
    :param str metrics_file: Filename in each experiment dir which contains metrics values.
    :return: {string}
    """
    table_tpl = """
        <table class="tr-link signals-rc-file w3-table w3-bordered w3-striped w3-border w3-hoverable tablesorter">
            <thead>
                <tr class="w3-green">
                    <th>Folder</th>
                    <th>Description</th>
                    {metrics_names}
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    """

    row_tpl = """
        <tr data-href='?experiment={exp_dir}'>
            <td>{exp_dir}</td>
            <td>{description}</td>
            {metrics_names}
        </tr>
    """

    # Get all metrics names
    metrics_names = get_metrics_names(base_dir, get_metrics_fcn, metrics_file)

    # Update table_template
    metric_names_tpl = ["<th>{}</th>".format(m) for m in metrics_names]
    table_tpl = table_tpl.format(metrics_names="".join(metric_names_tpl), rows="{rows}")

    # Update row_template
    metrics_names = [re.sub(r'\W+', '', m) for m in metrics_names]  # remove nonalpha (caused problems with **metrics)
    metric_names_tpl = ["<td>{{{}}}</td>".format(m) for m in metrics_names]
    row_tpl = row_tpl.format(metrics_names="".join(metric_names_tpl), exp_dir="{exp_dir}", description="{description}")

    # Iterate over experiments and get html row for each
    formatter = PartialFormatter()
    rows = []
    for exp_dir, exp_path, date_changed in list_experiments(base_dir):
        # Load metrics
        metrics_file_path = os.path.join(exp_path, metrics_file)
        metrics_rows = get_metrics_fcn(metrics_file_path)

        for metrics in metrics_rows:
            # remove nonalpha (caused problems with **metrics)
            metrics = {re.sub(r'\W+', '', k): v for k, v in metrics.items()}

            row = formatter.format(
                row_tpl,
                exp_dir=exp_dir,
                description=DescriptionToHtml.get_description_html(exp_path),
                **metrics
            )
            rows.append(row)

    # Fill rows in the table template
    table = table_tpl.format(rows="\n".join(rows))

    return table


def get_metrics_names(base_dir, get_metrics_fcn, metrics_file):
    metrics_names = set()
    for exp_dir, exp_path, date_changed in list_experiments(base_dir):
        metrics_file_path = os.path.join(exp_path, metrics_file)
        for metrics in get_metrics_fcn(metrics_file_path):
            exp_metric_names = metrics.keys()
            metrics_names |= set(exp_metric_names)
    metrics_names = sorted(metrics_names)
    return metrics_names


def html_navigation(base_dir, selected_experiment=None):
    """Build HTML navigation (left menu).

    :param base_dir: parent folder in which to look for an experiment folders
    :param selected_experiment: file name of selected experiment
    :return: {string}
    """
    # Header experiment links
    header = u"""
    <header class="w3-container w3-dark-grey">
       <h5><a href="/">Experiments</a></h5>
    </header>
    """

    items = []
    for exp_dir, exp_path, date_changed in list_experiments(base_dir):
        classes = []
        if exp_dir == selected_experiment:
            classes.append('w3-green')

        if not path.exists(path.join(exp_path, "flexp_info.txt")):
            classes.append("running")
        elif path.exists(path.join(exp_path, ".FAIL")):
            classes.append("failed")
        items.append(
            u"""<div class='' style='white-space: nowrap;'>
            <div onclick=\"$('#dialog-confirm').data('folder', '{exp_dir}').dialog('open')\" class=\"delete\">&nbsp;</div>
            <div 
                onclick=\"$('#new_name').val('{exp_dir}');$('#dialog-rename').data('folder', '{exp_dir}').dialog('open')\" 
                class=\"edit padding-right\">
                &nbsp;
            </div>
            <a class=\"{classes} left-margin\" href=\"?experiment={exp_dir}\" title=\"{title}\" style='padding-left:2px'>{exp_dir}</a>
            </div>""".format(
                exp_dir=exp_dir,
                title=DescriptionToHtml.get_description_html(exp_path,
                                                             replace_newlines=False),
                classes=" ".join(classes)))
    return header + "\n".join(items)


def html_anchor_navigation(base_dir, experiment_dir, modules):
    """Build header of an experiment with links to all modules used for rendering.

    :param base_dir: parent folder in which to look for an experiment folders
    :param experiment_dir: experiment folder
    :param modules: list of all loaded modules
    :return: str
    """
    return "\n".join((
        """<header class="w3-container w3-dark-grey">
             <h5><a href='#'>{folder}</a></h5>
           </header>""".format(folder=experiment_dir),
        "\n".join("""
            <div style='white-space: nowrap;'>
                <div class=\"show toggle-cookie padding-right\" data-toggle='toggle-{id}-all' data-class-off='no-show'>&nbsp;</div>
                <a class='' href='#{module_title}'>{module_title}</a>
            </div>""".format(
            folder=experiment_dir,
            module_title=module.title,
            id=module.id)
                  for module in modules),
        "<hr />"
    ))


def list_experiments(base_dir):
    """Return list of tuples(experiment_directory, experiment_absolute_path,
    last modified time) sorted by modification time.

    :param base_dir: parent folder in which to look for an experiment folders
    :return: list[tuple[str, str, int]]
    """
    return sorted([
        (exp_dir,
         path.join(base_dir, exp_dir),
         os.path.getmtime(path.join(base_dir, exp_dir)))
        for exp_dir in os.listdir(base_dir)
        if path.isdir(path.join(base_dir, exp_dir))],
        key=lambda x: x[2], reverse=True)


def return_type_list_of_dicts(fcn, return_on_fail=None):
    def wrapper(*args, **kwargs):
        try:
            out = fcn(*args, **kwargs)
            assert isinstance(out, list), type(out)
            assert len(out) > 0, len(out)
            for item in out:
                assert isinstance(item, dict), type(item)
            return out
        except Exception as e:
            logging.warning("Exception in {}: {}".format(fcn.__name__, e))
            return return_on_fail

    return wrapper


class NoCacheStaticHandler(tornado.web.StaticFileHandler):
    """Necessary class for Tornado."""

    def should_return_304(self):
        return False


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--port', '-p', default=7777,
              help='Port where to run flexp browser')
@click.option('--experiments_dir', '-d', default=os.getcwd(), type=click.Path(),
              help='path to directory with experiments')
def main(port, experiments_dir):
    """Console entry point launched by flexp-browser command."""
    setup_logging("info")
    run(port=port,
        experiments_dir=experiments_dir)


if __name__ == "__main__":
    main()
