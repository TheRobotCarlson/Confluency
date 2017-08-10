# Confluency
A simple api for accessing the Confluence REST API

No need to keep track of IDs or worry about anything going on behind the scenes. Confluency provides a simple interface to the Confluence REST api with simple caching to accelerate repeated requests.


## Installation
This package can be installed from pip using the following:
```
pip install Confluency
```

## Usage
Some examle functions are shown.  Get, add, and delete exist for each type of operation.

```python
from Confluency import ConfluenceApi

api = ConfluenceApi(base_url=BASE_URL, auth=auth)

response = api.get_page(space_key=space_key, page_name=page)  # as json
response = api.add_page(space_key=space_key, page_name=page, body=body)  # body is html

response = api.add_space(space_key=space_key, space_name=parent_name, description=content)

response = api.add_document(space_key=space_key, page_name=page, document_loc=document_loc)

response = api.add_child(space_key=space_key, page_name=page, parent_name=parent_name)
```

