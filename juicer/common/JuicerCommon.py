# -*- coding: utf-8 -*-
import json
import requests

class JuicerCommon(object):
    def __init__(self, connect_params):
        self.auth = (connect_params['username'], connect_params['password'])
        self.headers = {'content-type': 'application/json'}        
    
    def delete(self, url=""):
        return requests.delete(url, auth=self.auth, headers=self.headers,
                               verify=False)

    def get(self, url=""):
        return requests.get(url, auth=self.auth, headers=self.headers,
                            verify=False)

    def post(self, url="", data={}):
        return requests.post(url, json.dumps(data), auth=self.auth,
                             headers=self.headers, verify=False)

    def put(self, url="", data={}):
        return requests.put(url, json.dumps(data), auth=self.auth,
                            headers=self.headers, verify=False)
