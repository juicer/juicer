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

        self.connectors = juicer.utils.get_login_info()

    def create_repo(self, query='/repositories/', output=[]):
        data = {'name': self.args.name,
                'arch': 'noarch'}

        for env in self.args.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])

            _r = self.connectors[env].put(query, data)

            if _r.status_code == 201:
                output.append("Created repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()

        return output

    def create_user(self, query='/users/', output=[]):
        data = {'login': self.args.login,
                'password': self.args.password,
                'name': self.args.name}
        for env in self.args.envs:
            if juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` aleady exists in %s" % (self.args.login, env))
                continue
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == 201:
                    output.append("Successfully created user `%s` with login `%s` in %s" % (self.args.name, self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    def delete_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].delete(url)
            if _r.status_code == 202:
                output.append("Deleted repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def delete_user(self, query='/users/', output=[]):
        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].delete(url)
                if _r.status_code == 200:
                    output.append("Successfuly deleted user with login `%s` in %s" % (self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    def list_repos(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            _r = self.connectors[env].get(query)
            if _r.status_code == 200:
                for repo in simplejson.loads(str(_r.content)):
                    output.append(repo['id'])
            else:
                _r.raise_for_status()
        return sorted(list(set(output)))

    def show_repo(self, query='/repositories/', output=[]):
        for env in self.args.envs:
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                output.append(simplejson.loads(str(_r.content)))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output=[]):
        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].get(url)
                if _r.status_code == 200:
                    output.append(simplejson.loads(str(_r.content)))
                else:
                    _r.raise_for_status()
        return output
