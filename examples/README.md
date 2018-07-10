# Examples using flexp

All examples stores results in experiments folder `{path_to_flexp}/examples/experiments/`.

## Run flexp-browser

To see the experiment results run flexp-browser and open your browser
at selected port:

```bash
cd {path_to_flexp}/examples/experiments/
flexp-browser --port 7777
```

[See more about flexp-browser](/flexp/browser/README.md)


## Flexp, flow example
### Train a classifier on Iris dataset.

[classify_iris.py](/examples/classify_iris.py) shows how to setup
experiment with flexp, loading data and training and evaluating a classifier.

[Scikit-learn](http://scikit-learn.org/) neccessary to run the example.

```bash
pip install -U scikit-learn
cd {path_to_flexp}/examples/
python classify_iris.py --desc test_clf
```
