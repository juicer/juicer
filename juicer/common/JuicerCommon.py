# -*- coding: utf-8 -*-
import juicer.utils
import requests

class JuicerCommon(object):
    def __init__(self, connect_params):
        self.base_url = connect_params['base_url']
        self.auth = (connect_params['username'], connect_params['password'])
        self.headers = {'content-type': 'application/json'}

    def delete(self, url=""):
        url = self.base_url + url
        return requests.delete(url, auth=self.auth, headers=self.headers,
                               verify=False)

    def get(self, url=""):
        url = self.base_url + url
        return requests.get(url, auth=self.auth, headers=self.headers,
                            verify=False)

    def post(self, url="", data={}):
        url = self.base_url + url
        return requests.post(url, juicer.utils.create_json_str(data), auth=self.auth,
                             headers=self.headers, verify=False)

    def put(self, url="", data={}):
        url = self.base_url + url
        return requests.put(url, juicer.utils.create_json_str(data), auth=self.auth,
                            headers=self.headers, verify=False)
