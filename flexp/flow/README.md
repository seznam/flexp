# flow
flow brings [flow-based-programming](https://wiki.python.org/moin/FlowBasedProgramming) paradigm into your projects.

flow forces developers to divide the program into small chunks of code. 
This prevents having classes with a lot of methods, very complicated class structure and dependencies and spaghetti code. 
We hope to increase readability of the code, consistency of the whole program and robustness to changes in interfaces.

Core element of flow is `Chain`, a sequence of operations performed on the `data`. 
Chain consists of self-contained `modules`, each module modifies the data.
Modules are either classes with method `process` that takes single argument `data` or functions.

Data that flow between the modules is any structure containing the data. 
Usually, it is either a plain dict or a class.
In some cases, having data as list may be suitable.


## Dependency checking
flexp has a very basic checking of dependencies between modules. 
It ensures basic compatibility of the chain, preventing cases when a module expects data provided by other module.

Modules may have `provides` and `requires` fields to indicate which fields are provided and which are expected by the module.
Usually, `provides` is a list of keys in data created by the module. 

But, it may be thought of as a list of ids of provided capabilities. 
For example a module for lemmatization modifies `data['tokens']`, but its `provides` is `['lemmas']`. 
Other module `requires` `lemmas`, but only to indicate that the tokens in `data['tokens']` are expected to be lemmatized.   


## Example usage
The script below shows the structure of a program that processes queries and does linear regression on tf-idf features. It can be run in the `examples` directory as `python simple_example.py`.
The modules are defined in [examples/simple_modules.py](examples/simple_modules.py).
```python
from flexp.flow import Chain

from simple_modules import (
    LoadData, Lowercase, TrainTestSplit, TfIdf, Train, Eval
)

# Create the chain to load the data, lowercase and tokenize it.
file_name = "queries.tsv"
data_chain = Chain([
    LoadData(file_name),
    Lowercase(),
    TfIdf(),
])

# data["id"] should contain all info required to replicate the experiment.
data = {"id": file_name}
data_chain.process(data)
data_chain.close()

# Train and evaluate a classifier
train_chain = Chain([
    # Create data["train"] and data["dev"]
    TrainTestSplit(),
    # Train our classifier on data["train"]
    Train(),
    # Evaluate the classifier and store the results in the experiment folder
    # using flexp.get_file_path("results.csv")
    Eval(),
])
train_chain.process(data)
train_chain.close()
```

## Example module
Modules must have `process` method, other things are optional. This is the structure of a module.
```python
class Module(object):
    # optional
    # This modules creates following keys in data:
    provides = []
    # optional
    # This module expects these fields to be present in data. They should be provided by modules before this one. 
    requires = []

    # required
    def process(self, data):
        """
        :param data: Data modified by the module
        :type data: dict|object 
        """
        # operations on the data dict
        pass

    # optional
    def close(self):
        # free resources
        pass
```
For a more concrete example, see [examples/simple_modules.py](examples/simple_modules.py).

### PickleCache

PickleCache is used to cache a long running chain. 

It takes several things into account, when checking if it contains the results. 
The key to cache is composed of two strings:

1) `data['id']` - name of the files it reads, size of the data, ... should be here. 
This is your responsibility to fill in, as the program can't know what is relevant and what not.

2) Hash of the chain it caches - to be sure it returns the result of correct chain, all modules in the chain are hashed.
 The hash of the chain is computed from string representation of its modules. 

 Each module string contains info about:
   * module class
   * string of attributes names and values of the module using __dict__.
    

Caveats:    
* When computing the string representation of the chain, the recursive call on all attributes of modules can be dangerous and/or slow.
Storing large dictionaries in the module significantly slows down computation of the hash.
* It uses pickle to store `data` and to compute the hash of the chain, so both things have to be pickleable. 
Common issue is an open lmdb database in the module, which is not pickleable. 
Solution for this is to store only the name of the database and open it in the `process()` method.



```python
    from flexp.flow import Chain
    from flexp.flow.cache import PickleCache
    file_name = "dotazy.tsv"
    chain = Chain([
        LoadData(file_name)
    ])
    cached_chain = PickleCache('cached_data/', 'id', chain)
    cached_chain.process({'id': file_name})
    cached_chain.close()
```


If you have several PickleCache modules in a sequence then you can
use CachingChain.

- if update_data_id is True then it updates data key after each module
that has `UpdateDataId` class attribute (see TestModule in example).

- CachingChaing look for last PickleCache module that already has cache, skip previous modules

```python

class TestModule:

    UpdateDataId = "id"

    def __init__(self, attr1):
        self.attr1 = attr1

    def process(self, data):
        pass

class EmptyModule:

    def __init__(self, attr1, attr2):
        self.attr1 = attr1
        self.attr2 = attr2

    def process(self, data):
        pass

my_chain = CachingChain([
    # PickleCache ALWAYS change data key
    PickleCache("cached_pkl", "id", [TestModule(12, 14, 18)]),  # key update
    PickleCache("cached_pkl", "id", [TestModule(12, 10, 18)]),  # key update
    EmptyModule(12, 12, 18),  # no key update
    TestModule(12, 12, 18),  # key update (UpdateDataId is in TestModule)
    ], update_data_id='id')
```
