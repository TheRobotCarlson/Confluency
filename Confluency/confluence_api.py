import ssl
import requests
import os
import json
from urllib.parse import urlencode


class ConfluenceApi(object):

    def __init__(self, base_url, auth, verify=True, cert=None):
        self.API_URL = base_url + "rest/api"
        self.CONTENT_URL = self.API_URL + "/content"
        self.SPACE_URL = self.API_URL + "/space"
        self._session = requests.Session()
        self._session.auth = auth
        self._session.verify = verify
        self._session.headers.update({"Content-Type": "application/json"})
        self._session.cert = cert
        # requests_cache.install_cache(cache_name="cache", backend="memory")
        self.cache = {}

    def add_to_cache(self, space_key, page_name, response):
        if space_key not in self.cache:
            self.cache[space_key] = {}

        self.cache[space_key][page_name] = response

    def get_from_cache(self, space_key, page_name):
        if self.in_cache(space_key=space_key, page_name=page_name):
            return self.cache[space_key][page_name]
        else:
            return None

    def remove_from_cache(self, space_key, page_name):
        if self.in_cache(space_key=space_key, page_name=page_name):
            self.cache[space_key].pop(page_name)

    def in_cache(self, space_key, page_name):
        return space_key in self.cache and page_name in self.cache

    # def get_page_with_cache(self, space_key, page_name):
    #     page_return = self.get_from_cache(space_key=space_key, page_name=page_name)
    #
    #     if page_return is None:
    #         page_return = self.get_page(space_key=space_key, page_name=page_name)
    #         self.add_to_cache(space_key=space_key, page_name=page_name, response=page_return)
    #
    #     return page_return
    #
    # def delete_page_with_cache(self, space_key, page_name):
    #     if self.in_cache(space_key=space_key, page_name=page_name):
    #         self.remove_from_cache(space_key=space_key, page_name=page_name)
    #         self.delete_page(space_key=space_key, page_name=page_name)

    def get_page(self, space_key, page_name, with_cache=True):
        page_return = None

        if with_cache:
            page_return = self.get_from_cache(space_key=space_key, page_name=page_name)

        if page_return is None:
            payload = {"title": page_name, "spaceKey": space_key, "expand": "body.storage,version,ancestors"}

            url = self.CONTENT_URL + "?" + urlencode(payload)
            page_return = self._session.get(url).json()

            if page_return["size"] is 0:
                print("There is no page in {} with the name {}".format(space_key, page_name))
                page_return = None

        if with_cache:
            self.add_to_cache(space_key=space_key, page_name=page_name, response=page_return)

        return page_return

    def add_page(self, space_key, page_name, body, ancestor_names=(), with_cache=True):

        if len(ancestor_names) > 0:
            _ancestors = []
            for ancestor in ancestor_names:
                _ancestors.append({"id": self.get_page_id(space_key=space_key, page_name=ancestor,
                                                          with_cache=with_cache)})

            payload = {"title": page_name, "version": {"number": 1},
                       "type": "page",
                       "space": {"key": space_key},
                       "ancestors": _ancestors,
                       "body": {"storage": {"value": body, "representation": "storage"}}}
        else:
            payload = {"title": page_name, "version": {"number": 1},
                       "type": "page",
                       "space": {"key": space_key},
                       "body": {"storage": {"value": body, "representation": "storage"}}}

        page_return = self._session.post(self.CONTENT_URL, data=json.dumps(payload))

        return page_return.json()

    def update_page_body(self, space_key, page_name, body, with_cache=True):
        page_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)
        version = self.get_page_version(space_key=space_key, page_name=page_name, with_cache=with_cache)

        payload = {"title": page_name, "version": {"number": version + 1}, "type": "page",
                   "body": {"storage": {"value": body, "representation": "storage"}}}

        r = self._session.put(self.CONTENT_URL + "/" + page_id, data=json.dumps(payload))

        if with_cache:
            self.remove_from_cache(space_key=space_key, page_name=page_name)

        return r.json()

    def copy_page_body(self, space_key_ref, space_key, page_name, with_cache=True):
        body = self.get_page(space_key=space_key_ref, page_name=page_name, with_cache=with_cache)["results"][0][
            "body"]

        response = self.update_page_body(space_key=space_key, page_name=page_name, body=body, with_cache=with_cache)

        return response

    def delete_page(self, space_key, page_name, with_cache=True):
        if with_cache:
            self.remove_from_cache(space_key=space_key, page_name=page_name)

        page_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)

        if page_id is None:
            return

        return self._session.delete(self.CONTENT_URL + "/" + page_id)

    def get_space(self, space_key):
        payload = {"spaceKey": space_key}
        page = self._session.get(self.SPACE_URL, payload=json.dumps(payload))

        return page.json()

    def add_space(self, space_key, space_name, description, with_cache=True):

        if with_cache:
            self.cache[space_key] = {}

        payload = {"key": space_key,
                   "name": space_name,
                   "type": "global",
                   "description": {
                       "plain": {
                           "value": description,
                           "representation": "plain"
                       }
                    }
                   }

        page = self._session.post(self.SPACE_URL, data=json.dumps(payload))

        return json.loads(page.content)

    def delete_space(self, space_key, with_cache=True):
        if with_cache and space_key in self.cache:
            self.cache.pop(space_key)
        return self._session.delete(self.SPACE_URL + "/" + space_key)

    def get_page_id(self, space_key, page_name, with_cache=True):
        content = self.get_page(space_key=space_key, page_name=page_name, with_cache=with_cache)

        if content is not None:
            return content["results"][0]["id"]
        else:
            return None

    def get_page_version(self, space_key, page_name, with_cache=True):
        content = self.get_page(space_key=space_key, page_name=page_name, with_cache=with_cache)

        if content["size"] is not 0:
            return content["results"][0]["version"]["number"]
        else:
            print("There is no page with that page name.")

    def add_child(self, space_key, page_name, parent_name, with_cache=True):
        child_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)
        version = self.get_page_version(space_key=space_key, page_name=page_name, with_cache=with_cache)
        parent_id = self.get_page_id(space_key=space_key, page_name=parent_name, with_cache=with_cache)
        payload = {"version": {"number": version + 1}, "content": {"ancestors": [{"id": parent_id}]}, "type": "page"}

        r = self._session.put(self.CONTENT_URL + "/" + child_id, data=json.dumps(payload))

        if with_cache:
            self.remove_from_cache(space_key=space_key, page_name=page_name)

        return r.json()

    def add_document(self, space_key, page_name, document_loc, with_cache=True):

        files = {"file": open(document_loc, 'rb'), "comment": "Generated Doc"}

        page_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)

        url = self.CONTENT_URL + "/" + page_id + "/child/attachment"

        headers = self._session.headers
        self._session.headers = ({"X-Atlassian-Token": "nocheck"})
        response = self._session.post(url, files=files)

        self._session.headers = headers

        return response

    def update_document(self, space_key, page_name, document_loc, with_cache=True):
        files = {"file": open(document_loc, 'rb'), "comment": "New Generated Doc"}
        page_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)

        url = self.CONTENT_URL + "/" + page_id + "/child/attachment"

        document_name = os.path.split(document_loc)[-1]
        att_id = self.get_document_id(space_key=space_key, page_name=page_name,
                                        document_name=document_name, with_cache=with_cache)

        headers = self._session.headers
        self._session.headers = ({"X-Atlassian-Token": "nocheck"})
        response = self._session.post(url + "/{}/data".format(att_id), files=files)

        self._session.headers = headers

        return response

    def get_document_id(self, space_key, page_name, document_name, with_cache=True):

        page_id = self.get_page_id(space_key=space_key, page_name=page_name, with_cache=with_cache)
        p = self.CONTENT_URL + "/" + page_id + "/child/attachment"
        p += "?filename={}&expand=version,container".format(document_name)

        response = self._session.get(p).json()

        if response["size"] is not 0:
            return response["results"][0]["id"]
        else:
            return None

    # def copy_page(self, space_key_a, page_name_a, space_key_b, page_name_b, with_replacements=(), with_cache=True):
