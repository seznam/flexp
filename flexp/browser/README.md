# flexp-browser
flexp browser is a tool that displays a content of a folder in a web browser. 
It is used to show experiment result. 

![Flexp-browser preview](/browser.png)

With flexp browser you can:
- divide experiment content to sections,
- easy display/hide some content,
- edit some files just from web browser,
- edit experiment name,
- remove experiment

## How to use flexp-browser

### 1. Simple way

Uses basic display modules (image, csv, txt, all_files) with
default display configurations.

```bash
cd {path_to_flexp}/examples/experiments/
flexp-browser --port 7777
```

### 2. Own display configuration
Allows me to:
- group files together based on filename regexp
- use other predefined modules.

Edit [browse.py](/examples/experiments/browse.py) as you wish and run:
```bash
cd {project_dir}/examples/experiments/
python browse.py --port 7777
```

### 3. Create own module
If you have some specific format of a file you can write own module that displays the
file in a desired way. Check [browse_module.py](/examples/experiments/browse_module.py) how to write your own module.


```bash
cd example/
python browse_module.py --port 7777
```

### 4. Create own metric parser
For easy experiment comparision, metric values are shown in experiment list,
if experiment folders contains `metrics.csv`.

![Flexp-browser experiments preview](/browser_experiments.png)

This file is parsed by default following way: 
 - first row (header) is skipped
 - first column is used as metric names
 - second column is used as metric values

If your `metrics_filename` or it's structure is different, you can use own parser
by providing `metrics_filename` and/or `get_metrics_fcn`. 
 Check [browse_metrics.py](/examples/experiments/browse_metrics.py) for an example.

```bash
cd example/
python browse_metrics.py --port 7777
```


### 5. Use own display configuration for each experiment
You can create specific display configuration for each experiment. You just need to create `custom_flexp_chain.py`
_in experiment dir_ in the following format:

```python
from flow.flexp_browser.html.generic import ImagesToHtml, CsvToHtml

def get_chain():
    chain = [
        ImagesToHtml(),
        CsvToHtml(file_name_pattern="metrics.csv", title="Metrics"),
    ]
    return chain
```


## List of all modules

There is a list of provided modules. You can also create your custom module 
[in this way](examples/flexp_browser#3-create-own-module).

* **TxtToHtml**

Print file content. Text files can be edited in browser when parameter `editable` is `True`
```python
from flexp.browser.html.generic import TxtToHtml
TxtToHtml(file_name_pattern="(description.txt)", title="Description", editable=False),
```

* **FlexpInfoToHtml**

Print content of `flexp_info.txt` with link to experiment log. Text files can be edited in browser when
 parameter `editable` is `True`
```python
from flexp.browser.html.generic import FlexpInfoToHtml
FlexpInfoToHtml()
```     

* **DescriptionToHtml**

Retrieve an description from `description.txt`.
```python
from flexp.browser.html.generic import DescriptionToHtml
DescriptionToHtml()
```     

* **TimeToHtml**

Show the duration of an experiment from log.txt.

```python
from flexp.browser.html.generic import TimeToHtml
TimeToHtml()
```     

* **CsvToHtml**

Print csv files to html. Important parameters:
- `max_rows`: number of displayed rows, use this **for big files**
- `max_files`: number of files (chosen by `file_name_pattern`)
- `delimiter`
- `quotechar`

```python
from flexp.browser.html.generic import CsvToHtml
CsvToHtml(file_name_pattern="metrics", title="Metrics", max_rows=300)
```     


* **ImagesToHtml**

Create HTML representation of all images from experiment folder.

```python
from flexp.browser.html.generic import ImagesToHtml
ImagesToHtml()
```    

* **StringToHtml**

Prints string given in constructor.

```python
from flexp.browser.html.generic import StringToHtml
StringToHtml("Some string that will be displayed")
```    

* **FilesToHtml**

Print list of files 

```python
from flexp.browser.html.generic import FilesToHtml
FilesToHtml()
```  

