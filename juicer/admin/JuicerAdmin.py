# -*- coding: utf-8 -*-
import juicer.common
import juicer.utils
import juicer.admin
import json
import requests
import simplejson

class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args

        connect_params = juicer.utils.get_login_info(self.args)
        
        self.jc = juicer.common.JuicerCommon(connect_params)
        
        self.base_url = connect_params['base_url']
        

    def create_repo(self, query='/repositories/', output=[]):
        data = {'name': self.args.name,
                'arch': 'noarch'}
        for env in self.args.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])
            url = self.base_url + query
            _r = self.jc.put(url, data)
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
        _r = self.jc.post(url, data)
        if _r.status_code == 201:
            output = "Successfully created user `%s` with login `%s`" % (self.args.name, self.args.login)
        else:
            _r.raise_for_status()
        return output

    def delete_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            _r = self.jc.delete(url)
            if _r.status_code == 202:
                output.append("Deleted repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def delete_user(self, query='/users/', output=""):
        url = "%s%s%s/" % (self.base_url, query, self.args.login)
        _r = self.jc.delete(url)
        if _r.status_code == 200:
            output = "Successfuly deleted user with login `%s`" % (self.args.login)
        else:
            _r.raise_for_status()
        return output

    def list_repos(self, query='/repositories/', output=[]):
        url = "%s%s" % (self.base_url, query)
        _r = self.jc.get(url)
        if _r.status_code == 200:
            for repo in simplejson.loads(str(_r.content)):
                output.append(repo['id'])
        else:
            _r.raise_for_status()
        return output

    def show_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_url, query, self.args.name, env)
            _r = self.jc.get(url)
            if _r.status_code == 200:
                output.append(simplejson.loads(str(_r.content)))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output=""):
        url = "%s%s%s/" % (self.base_url, query, self.args.login)
        _r = self.jc.get(url)
        if _r.status_code == 200:
            output = simplejson.loads(str(_r.content))
        else:
            _r.raise_for_status()
        return output
