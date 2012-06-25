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

        self.connectors = {}
        self.base_urls = {}
        for env in self.args.envs:
            connect_params = juicer.utils.get_login_info(self.args, env)
            self.connectors[env] = juicer.common.JuicerCommon(connect_params)
            self.base_urls[env] = connect_params['base_url']

    def create_repo(self, query='/repositories/', output=[]):
        """
        Create repository in specified environments
        """
        data = {'name': self.args.name,
                'arch': 'noarch'}
        for env in self.args.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])
            url = self.base_urls[env] + query
            _r = self.connectors[env].put(url, data)
            if _r.status_code == 201:
                output.append("Created repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def create_user(self, query='/users/', output=[]):
        """
        Create user in specified environments
        """
        data = {'login': self.args.login,
                'password': self.args.password,
                'name': self.args.name}
        for env in self.args.envs:
            if juicer.utils.user_exists_p(self.args, self.base_urls[env], self.connectors[env]):
                output.append("User with login `%s` aleady exists in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s" % (self.base_urls[env], query)
                _r = self.connectors[env].post(url, data)
                if _r.status_code == 201:
                    output.append("Successfully created user `%s` with login `%s` in %s" % (self.args.name, self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    # Do we want this or should puppet manage it? I think puppet.
    def create_role(self, query='/roles/', output=[]):
        data = {'name': self.args.name}
        for env in self.args.envs:
            if juicer.utils.role_exists_p(self.args, self.connectors[env]):
                output += "Role `%s` already exists in %s" % (self.args.name, env)
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == 200:
                    output.append("Successfully created role `` in %s" % (self.args.name, env))
                else:
                    _r.raise_for_status()
        return output

    def delete_repo(self, query='/repositories/', output=[]):
        """
        Delete repo in specified environments
        """
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_urls[env], query, self.args.name, env)
            _r = self.connectors[env].delete(url)
            if _r.status_code == 202:
                output.append("Deleted repository %s-%s" % (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def delete_user(self, query='/users/', output=[]):
        """
        Delete user in specified environments
        """
        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.base_urls[env], self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s%s/" % (self.base_urls[env], query, self.args.login)
                _r = self.connectors[env].delete(url)
                if _r.status_code == 200:
                    output.append("Successfuly deleted user with login `%s` in %s" % (self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    def list_repos(self, query='/repositories/', output=[]):
        """
        List repositories in specified environments
        """
        for env in self.args.envs:
            url = "%s%s" % (self.base_urls[env], query)
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                for repo in simplejson.loads(str(_r.content)):
                    output.append(repo['id'])
            else:
                _r.raise_for_status()
        return sorted(list(set(output)))

    def role_add(self, query='/roles/', output=[]):
        data = {'username': self.args.login}
        for env in self.args.envs:
            url = "%s%s/add/" % (query, self.args.role)
            _r = self.connectors[env].post(url, data)
            if _r.status_code == 200:
                output.append("Successfuly added user `%s` to role `%s` in %s" % (self.args.login, self.args.role, env))
            else:
                output.append("Could not add user `%s` to role `%s` in %s" % (self.args.login, self.args.role, env))
        return output

    def show_repo(self, query='/repositories/', output=[]):
        """
        Show repositories in specified environments
        """
        for env in self.args.envs:
            url = "%s%s%s-%s/" % (self.base_urls[env], query, self.args.name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                output.append(simplejson.loads(str(_r.content)))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output=[]):
        """
        Show user in specified environments
        """
        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.base_urls[env], self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s%s/" % (self.base_urls[env], query, self.args.login)
                _r = self.connectors[env].get(url)
                if _r.status_code == 200:
                    output.append(simplejson.loads(str(_r.content)))
                else:
                    _r.raise_for_status()
        return output

    def show_roles(self, query='/roles/', output=[]):
        for env in self.args.envs:
            url = query
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                output.append(simplejson.loads(str(_r.content)))
            else:
                _r.raise_for_status()
        return output
