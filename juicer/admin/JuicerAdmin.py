# -*- coding: utf-8 -*-
import juicer.utils
import juicer.admin
import json
import requests


class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args
        self.envs = self.args.envs

        connect_params = juicer.utils.get_login_info(self.args)

        self.base_url = connect_params['base_url']
        self.auth = (connect_params['username'], connect_params['password'])
        self.headers = {'content-type': 'application/json'}

    def put(self, url="", data={}):
        return requests.put(url, json.dumps(data), auth=self.auth,
                            headers=self.headers, verify=False)

    def get(self, url=""):
        return requests.get(url, auth=self.auth, headers=self.headers,
                            verify=False)

    def delete(self, url=""):
        return requests.delete(url, auth=self.auth, headers=self.headers,
                               verify=False)

    def create_repo(self, query='/repositories/'):
        data = {'name': self.args.name,
                'arch': 'noarch'}
        for env in self.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])
            url = self.base_url + query
            r = self.put(url, data)
            print r.status_code, r.content

    def show_repo(self, query='/repositories/'):
        for env in self.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            print url
            print "base_url", self.base_url
            print "query", query
            print "name", self.args.name
            print "env", env
            r = self.get(url)
            print r.status_code, r.content

    def delete_repo(self, query='/repositories/'):
        for env in self.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            r = self.delete(url)
            print r.status_code, r.content
