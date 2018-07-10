#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FILE         $Id$
AUTHOR       Alan Eckhardt <alan.eckhardt@firma.seznam.cz>

Copyright (c) 2017 Seznam.cz, a.s.
All rights reserved.
"""
import argparse
import csv
import logging as log
import os
import shutil
import sys

from sklearn import datasets
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from flexp import flexp
from flexp.flexp.core import RWXRWXRWX
from flexp.flow import Chain
from flexp.flow.cache import PickleCache


class DownloadDataset:
    """
    Download dataset of given name.
    """

    def __init__(self, dataset_name="iris"):
        """
        :param str dataset_name: Name of the dataset to download
        """
        self.dataset_name = dataset_name

    def process(self, data):
        """
        :param dict data:
        :return:
        """
        try:
            result = getattr(datasets, 'load_' + self.dataset_name)()
        except:
            log.error("No such dataset {}!".format(self.dataset_name))
            raise StopIteration
        data['data'] = result


def split(data):
    """
    Splits data into train and test sets.
    :param data:
    :return:
    """
    x_train, x_test, y_train, y_test = train_test_split(
        data['data'].data, data['data'].target, test_size=0.2, random_state=42)

    data["train"] = (x_train, y_train)
    data["test"] = (x_test, y_test)
    log.debug("Split into {} train and {} test examples.".format(len(x_train), len(x_test)))


class Train:
    """
    Trains given classifier on training data.
    """

    def __init__(self, classifier):
        """
        :param object classifier: Scikit learn classifier to use.
        """
        self.classifier = classifier

    def process(self, data):
        """
        :param dict data:
        :return:
        """
        self.classifier.fit(data['train'][0], data['train'][1])
        data['predictions'] = self.classifier.predict(data['test'][0])

        # Store predictions in the experiment folder
        with open(flexp.get_file_path("predictions.csv"), "w") as f:
            f.write("\n".join([str(row) for row in data['predictions']]))


def evaluate_classifier(data):
    """
    Evaluates the predictions and stores the results in experiment directory.
    :param data:
    :return:
    """
    precision, recall, fscore, support = precision_recall_fscore_support(data['test'][1], data['predictions'], average='micro')

    # Store results in the experiment folder
    with open(flexp.get_file_path("results.csv"), "w") as f:
        w = csv.writer(f, dialect=csv.unix_dialect)
        w.writerow(["Precision", "Recall", "Fscore"])
        w.writerow([str(num) for num in [precision, recall, fscore]])


def clean_experiment_folder(folder):
    """
    Removes all from given experiment folder.
    :param str folder: Path to experiment folder.
    :return:
    """
    import os
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def main():
    """ Evaluates signals for estimating text relevance."""
    parser = argparse.ArgumentParser(description='''Downloads iris dataset and trains a classifier.''', add_help=False)
    parser.add_argument('--dataset_name', type=str, required=False, default="iris", help='Name of the dataset to use. Defaults to iris.')
    parser.add_argument('--desc', type=str, required=False, default="test", help='Description of the experiment.')
    args, unknown = parser.parse_known_args()

    project_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    # Experiments directory
    exps_dir = os.path.join(project_dir, "examples", "experiments")  # experiments

    # Initialize flexp
    flexp.setup(exps_dir, args.desc, with_date=True, default_rights=RWXRWXRWX)
    clean_experiment_folder(flexp.get_file_path(""))

    # Backup files into experiment folder.
    main_file = os.path.join(os.getcwd(), sys.argv[0])
    flexp.backup_files([main_file])
    flexp.backup_sources([os.path.join(project_dir, "flexp")])

    log.debug('Starting.')

    log.debug("Download and process data.")
    data = {"id": ".".join(map(str, [args.dataset_name]))}
    data_chain = [
        DownloadDataset(),
        split
    ]
    # Cache the split dataset
    data_chain = PickleCache("./cached_pkls", "id", data_chain)
    data_chain.process(data)

    log.debug("Train and evaluate the classifier.")
    from sklearn.tree import DecisionTreeClassifier
    eval_chain = Chain([
        Train(DecisionTreeClassifier(max_depth=5)),
        evaluate_classifier
    ])
    eval_chain.process(data)
    log.debug('Ended.')


if __name__ == "__main__":
    main()
