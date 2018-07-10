# flexp  

flexp is a tool for managing experiments. Every time you run experiment flexp creates folder with appropriate name and 
saves all results, time logs, etc. It also can backup files. 
We recommend to use it with [flexp_browser](/flexp/browser) (tool for displaying experiment info in browser).


# Usage
flexp is used in the beginning of the program to create or clean the experiment folder and setup logging. 

Like this:
```python
from flexp import flexp
import sys
import logging as log

# All the experiments are stored in "experiments" directory.
# This current one is in directory experiments/tf-idf-20180518-10-35-25/
# It also create file experiment.log.txt in the directory, where all logging is stored.
flexp.setup("./experiments", "tf-idf", with_date=True, loglevel=log.DEBUG,
          log_filename="experiment.log.txt")

# Store source codes
# Store the running program
flexp.backup_files([sys.argv[0], "simple_modules.py"])

# Store all files in these directories into a zip file
flexp.backup_sources([
    "./examples/",
    "./scripts/",
    "./demo/",
])

flexp.describe("Description of current experiment, usually set from command line.")

# This logs to both stderr and experiments/tf-idf.2018-05-28-09-08-40/experiment.log.txt
log.debug("flexp setup complete.")
```

Further in the program, flexp is used to store file in the experiment folder using flexp.get_file_path:
```python
import numpy as np
from flexp import flexp

def compute_rmse(data):
    rmse = np.sqrt(np.mean((data['predictions']-data['labels'])**2))
    with open(flexp.get_file_path("rmse.csv")) as f:
        f.write(str(rmse))
```
