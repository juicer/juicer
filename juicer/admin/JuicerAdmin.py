# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2012, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from juicer.common import Constants
import juicer.admin
import juicer.common
import juicer.utils
import juicer.utils.Log
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
                'arch': self.args.arch}

        juicer.utils.Log.log_debug("Create Repo: %s", self.args.name)

        for env in self.args.envs:
            data['relative_path'] = '/%s/%s/' % (env, self.args.name)
            data['id'] = '-'.join([self.args.name, env])

            _r = self.connectors[env].post(query, data)

            if _r.status_code == Constants.PULP_POST_CREATED:
                output.append("Created repository %s-%s" %\
                        (self.args.name, env))
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

        juicer.utils.Log.log_debug("Create User: %s ('%s')", self.args.login, self.args.name)

        for env in self.args.envs:
            if juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` aleady exists in %s" %
                              (self.args.login, env))
                continue
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    output.append(
                    "Successfully created user `%s` with login `%s` in %s" %
                                  (self.args.name, self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    def delete_repo(self, query='/repositories/', output=[]):
        """
        Delete repo in specified environments
        """
        juicer.utils.Log.log_debug("Delete Repo: %s", self.args.name)

        for env in self.args.envs:
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].delete(url)
            if _r.status_code == Constants.PULP_DELETE_ACCEPTED:
                output.append("Deleted repository %s-%s" %\
                        (self.args.name, env))
            else:
                _r.raise_for_status()
        return output

    def delete_user(self, query='/users/', output=[]):
        """
        Delete user in specified environments
        """
        juicer.utils.Log.log_debug("Delete User: %s", self.args.login)

        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output.append("User with login `%s` doesn't exist in %s" %
                              (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_OK:
                    output.append(
                        "Successfuly deleted user with login `%s` in %s" %
                                  (self.args.login, env))
                else:
                    _r.raise_for_status()
        return output

    def list_repos(self, query='/repositories/', output=[]):
        """
        List repositories in specified environments
        """
        juicer.utils.Log.log_debug("List Repos In: %s", ", ".join(self.args.envs))

        for env in self.args.envs:
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for repo in juicer.utils.load_json_str(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        output.append(repo['id'])
            else:
                _r.raise_for_status()
        return sorted(list(set(output)))

    def role_add(self, query='/roles/', output=[]):
        data = {'username': self.args.login}
        juicer.utils.Log.log_debug("Add Role '%s' to '%s'", self.args.role, self.args.login)

        for env in self.args.envs:
            url = "%s%s/add/" % (query, self.args.role)
            _r = self.connectors[env].post(url, data)
            if _r.status_code == Constants.PULP_POST_OK:
                output.append(
                        "Successfuly added user `%s` to role `%s` in %s" %
                              (self.args.login, self.args.role, env))
            else:
                output.append("Could not add user `%s` to role `%s` in %s" %
                              (self.args.login, self.args.role, env))
        return output

    def show_repo(self, query='/repositories/', output=[]):
        """
        Show repositories in specified environments
        """
        juicer.utils.Log.log_debug("Show Repo: %s", self.args.name)

        for env in self.args.envs:
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == Constants.PULP_GET_OK:
                output.append(juicer.utils.load_json_str(_r.content))
            else:
                _r.raise_for_status()
        return output

    def show_user(self, query='/users/', output={}):
        """
        Show user in specified environments
        """
        juicer.utils.Log.log_debug("Show User: %s", self.args.login)

        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                output[env] = ("User with login `%s` doesn't exist in %s" %
                                (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].get(url)
                if _r.status_code == Constants.PULP_GET_OK:
                    output[env] = juicer.utils.load_json_str(_r.content)
                else:
                    _r.raise_for_status()
        return output

    def list_roles(self, query='/roles/', output={}):
        """
        List roles in specified environments
        """
        juicer.utils.Log.log_debug("List Roles %s", ", ".join(self.args.envs))

        for env in self.args.envs:
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                output[env] = juicer.utils.load_json_str(_r.content)
            else:
                _r.raise_for_status()
        return output
