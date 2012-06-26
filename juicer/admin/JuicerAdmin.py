# -*- coding: utf-8 -*-
import juicer.common
import juicer.utils
import juicer.admin
import requests
import re

class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args

        self.connectors = juicer.utils.get_login_info()

    def create_repo(self, query='/repositories/', output=[]):
        """
        Create repository in specified environments
        """
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
        """
        Create user in specified environments
        """
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
        """
        Delete repo in specified environments
        """
        for env in self.args.envs:
            url = "%s%s-%s/" % (query, self.args.name, env)
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
        """
        List repositories in specified environments
        """
        for env in self.args.envs:
            _r = self.connectors[env].get(query)
            if _r.status_code == 200:
                for repo in juicer.utils.load_json_string(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        output.append(repo['id'])
            else:
                _r.raise_for_status()
        return sorted(list(set(output)))

    def role_add(self, query='/roles/', output=[]):
        data = {'username': self.args.login}
        for env in self.args.envs:
            url = "%s%s%s/add/" % (self.base_urls[env], query, self.args.role)
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
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                output.append(juicer.utils.load_json_string(_r.content))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output=[]):
        """
        Show user in specified environments
        """
        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" % (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].get(url)
                if _r.status_code == 200:
                    output.append(juicer.utils.load_json_string(_r.content))
                else:
                    _r.raise_for_status()
        return output

    def list_roles(self, query='/roles/', output=[]):
        for env in self.args.envs:
            url = self.base_urls[env] + query
            _r = self.connectors[env].get(url)
            if _r.status_code == 200:
                output.append(juicer.utils.load_json_string(_r.content))
            else:
                _r.raise_for_status()
        return output
