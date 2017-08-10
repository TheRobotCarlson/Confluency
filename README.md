# Confluency
A simple api for accessing the Confluence REST API

No need to keep track of IDs or worry about anything going on behind the scenes. Confluency provides a simple interface to the Confluence REST api with caching to accelerate repeated requests.


## Installation
This package can be installed from pip using the following:
```
pip install Confluency
```

## Usage

```python
from Confluency import ConfluenceApi

api = ConfluenceApi(base_url=BASE_URL, auth=auth)
```

