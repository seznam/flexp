import sys
import logging as log

from flexp.flow import Chain
from flexp import flexp

from simple_modules import (
    LoadData, Lowercase, TrainTestSplit, TfIdf, Train, Eval
)

# All the experiments are stored in "experiments" directory.
# This current one is in directory experiments/tf-idf-20180518-10-35-25/
flexp.setup("./experiments", "tf-idf", with_date=True)

# Store source codes
# Store the running program
flexp.backup_files([sys.argv[0], "simple_modules.py"])

# Store all files in these directories into a zip file
flexp.backup_sources(["../flexp/"])

flexp.describe("Query parameter prediction with TF-IDF and linear regression")

# Setup logging
log.debug("flow setup complete.")

# Create the chain to load the data, lowercase and tokenize it.
file_name = "example_queries.tsv"
data_chain = Chain([
    LoadData(file_name),
    Lowercase(),
    TfIdf(),
])

# data["id"] should contain all info required to replicate the experiment.
data = {"id": file_name}
data_chain.process(data)
data_chain.close()
log.debug("Data chain complete.")

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
log.debug("All done.")
