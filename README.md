# flexp - flexible experiments and data-flow programming framework

[![Build Status](https://travis-ci.com/seznam/flexp.svg?branch=master)](https://travis-ci.com/seznam/flexp)

flexp is a framework created by researchers for the researchers. 

Somebody comes to you and asks 'What was the result of that particular feature testing you tried a month ago? I need to know a precise number.'
In these cases, either cold sweat starts running down your back or you flip up the folder with the experiment and open results.csv.

flexp is aimed to 

1) simplify routine work and experiment management,

2) increase reproducibility of experiments,

3) introduce flow-based-programming in your project

4) create a web page with the results of the experiment.

It consists of three main parts:

| Component        | Provides| 
| ------------- |:-------------| 
| [flexp.flexp](/flexp/flexp/) | experiment runs that are consistent and replicable,|
| [flexp.browser](/flexp/browser/) | easy-to-find results from previous experiments via simple web application,|
| [flexp.flow](/flexp/flow/) | [flow-based-programming](https://wiki.python.org/moin/FlowBasedProgramming) paradigm into your projects,together with caching in flow.cache |

## Installation
Clone this repository.
Then, using setup.py:
```bash
python setup.py install
```
or using pip
```bash
pip install .
```

## Examples
To see flexp in action, head to the [examples folder](/examples/).


## Tests
* Install `Docker`
* Install `docker-compose`
* Run `docker-compose run tests`

## Env variables

- `FLEXP_LOGLEVEL` - intented to allow user to override log level set by flexp scripts. Can be set to loglevel names 
from python `logging`. Overrides log levels set by:
  - `flexp.flexp.setup`
  - `flexp.browser.utils.setup_logging`
