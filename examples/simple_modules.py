"""Modules used in the README example"""

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
import numpy as np

from flexp import flexp


class LoadData:
    """Load queries and targets from a tsv file"""
    provides = ["queries", "targets"]
    requires = []

    def __init__(self, file_name="example_queries.tsv"):
        """
        :param file_name: Path to the dataset to load
        :type file_name: str
        """
        self.file_name = file_name

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        # Read the file and split the lines into query and target value
        with open(self.file_name, 'r') as f:
            lines = f.readlines()
            lines = [line.strip().rsplit("\t", 1) for line in lines]
            queries, targets = zip(*lines)

        # Store queries and targets in data
        data['queries'] = queries
        data['targets'] = [float(t) for t in targets]

    def close(self):
        pass


class Lowercase:
    """Lowercase queries"""
    requires = ["queries"]
    provides = ["lowercased"]

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        data["lowercased"] = [q.lower() for q in data["queries"]]


class TfIdf:
    """Compute TF-IDF features for queries"""
    requires = ["lowercased"]
    provides = ["features"]

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        tfidf = TfidfVectorizer()
        data["features"] = tfidf.fit_transform(data["lowercased"])


class TrainTestSplit:
    """Split data to training and test set"""
    requires = ["features", "targets"]
    provides = ["train", "test"]

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        x_train, x_test, y_train, y_test = train_test_split(
            data["features"], data["targets"], random_state=42)
        data["train"] = (x_train, y_train)
        data["test"] = (x_test, y_test)


class Train:
    """Train a model and save its predictions on the test set"""
    requires = ["train", "test"]

    def __init__(self):
        self.regressor = LinearRegression()

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        self.regressor.fit(data["train"][0], data["train"][1])
        data['predictions'] = self.regressor.predict(data['test'][0])

        # Store predictions in the experiment folder
        with open(flexp.get_file_path("predictions.csv"), "w") as fout:
            fout.write("\n".join(str(row) for row in data['predictions']))


def rmse(a, b):
    """Root mean square error"""
    return np.sqrt(((a - b) ** 2).mean())


class Eval:
    """Evaluate the model"""
    requires = ["predictions"]

    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object
        """
        error = rmse(np.array(data['test'][1]), np.array(data['predictions']))

        with open(flexp.get_file_path("results.csv"), "w") as fout:
            print("RMSE: {}".format(error), file=fout)
