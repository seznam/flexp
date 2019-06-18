from flexp.browser import MainHandler
from os import path


class FeaturesHandler(MainHandler):

    def initialize(self, experiments_folder, html_chain):
        self.experiments_folder = experiments_folder
        self.html_chain = html_chain

    def create_title(self, experiment_folder, data):
        annotation_id = data['annotation_id']
        return "<h1>Features for {}</h1>".format(annotation_id)

    def create_navigation(self, navigation_html, experiment_folder, experiment_path, data):
        return navigation_html

    def get(self):
        annotation_id = self.get_argument("id", default="")

        # if not path.isdir(experiment_path):
        #     experiment_folder = ""

        data = {"experiment_path": "",  # experiment_path,
                "experiment_folder": "",  # experiment_folder,
                "html": [],
                "header": dict(),
                "scripts": dict(),
                "annotation_id": annotation_id,
                }

        self.create_page("", "", data)

    def create_content(self, experiment_folder, data):
        annotation_id = data['annotation_id']

        content_html = ""
        content_html += "<br>{}".format(annotation_id)
        content_html += '<br><table class="w3-table w3-bordered w3-striped w3-border w3-hoverable w3-card-2"> ' \
        '<colgroup> <col span="1" style="width: 50%;"> <col span="1" style="width: 50%;"> </colgroup> ' \
        '<thead><tr class="w3-green">' '<th class="header">Feature name</th><th class="header">Value</th></tr>' \
        '</thead><tbody> {}</tbody></table>'.format(''.join(["<tr><td>{}</td><td>{}</td>".format(feature_name, feature)
                                                             for feature_name, feature in [['f1', 0.3], ['f1', 0.3],
                                                                                           ['f1', 0.3]]]))

        return content_html
