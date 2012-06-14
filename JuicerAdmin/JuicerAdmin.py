# -*- coding: utf-8 -*-
import JuicerAdmin
import httplib2
import urllib

class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args
        self._http = httplib2.Http(disable_ssl_certificate_validation=True)
        self.envs = self.args.envs

        # Some default shit, read this in from yaml in util.py
        connect_params = {'user': 'admin', 
                          'password': 'admin',
                          'base_url': 'https://snarl.rdu.redhat.com/pulp/api'}

        self._http.add_credentials(connect_params['user'], connect_params['password'])
        self.base_url = connect_params['base_url']

    def read(self, url="", method='GET', params={}, headers={}):
        # Returns (response, content)
        return self._http.request(url, method, urllib.urlencode(params), headers)
        
    def create_repo(self):
        params = { 'arch': 'noarch',
                   'feed': '',
                   'publish': True,
                   'name': 'derp-test' }

        method = 'POST'
        query = '/repositories/'
        url = self.base_url + query
        headers = {'Content-type': 'application/x-www-form-urlencoded'} 
        
        for env in self.envs:
            params['id'] = '-'.join([params['name'], env])
            params['relative_path'] = "/%s/%s/" % (env, params['name'])
            (response, content) = self.read(url, method, params, headers)
            print response
            print content
