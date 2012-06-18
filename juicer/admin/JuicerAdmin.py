# -*- coding: utf-8 -*-
import juicer.utils
import juicer.admin
import json
import requests


class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args

        connect_params = juicer.utils.get_login_info(self.args)

        self.base_url = connect_params['base_url']
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

    def create_repo(self, query='/repositories/', output=[]):
        data = {'name': self.args.name,
                'arch': 'noarch'}
        for env in self.args.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])
            url = self.base_url + query
            _r = self.put(url, data)
            if _r.status_code == 201:
                output.append("Created repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def create_user(self, query='/users/', output=""):
        data = {'login': self.args.login,
                'password': self.args.password,
                'name': self.args.name}
        url = "%s%s" % (self.base_url, query)
        _r = self.post(url, data)
        if _r.status_code == 201:
            output = "Successfully created user `%s` with login `%s`" % (self.args.name, self.args.login)
        else:
            _r.raise_for_status()
        return output

    def delete_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            _r = self.delete(url)
            if _r.status_code == 202:
                output.append("Deleted repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def delete_user(self, query='/users/', output=""):
        url = "%s%s%s/" % (self.base_url, query, self.args.login)
        _r = self.delete(url)
        if _r.status_code == 200:
            output = "Successfuly deleted user with login `%s`" % (self.args.login)
        else:
            _r.raise_for_status()
        return output

    def list_repos(self, query='/repositories/', output=""):
        url = "%s%s" % (self.base_url, query)
        _r = self.get(url)
        if _r.status_code == 200:
            output=str(_r.content)
        else:
            _r.raise_for_status()
        return output

    def show_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            _r = self.get(url)
            if _r.status_code == 200:
                output.append(str(_r.content))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output=""):
        url = "%s%s%s/" % (self.base_url, query, self.args.login)
        _r = self.get(url)
        if _r.status_code == 200:
            output = str(_r.content)
        else:
            _r.raise_for_status()
        return output
