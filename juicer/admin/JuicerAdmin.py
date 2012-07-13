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

        (self.connectors, self._defaults) = juicer.utils.get_login_info()

    def create_repo(self, query='/repositories/'):
        """
        Create repository in specified environments
        """
        data = {'name': self.args.name,
                'arch': self.args.arch}

        if self.args.feed:
            data['feed'] = self.args.feed

        juicer.utils.Log.log_debug("Create Repo: %s", self.args.name)

        for env in self.args.envs:
            if juicer.utils.repo_exists_p(self.args, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` already exists in %s... skipping!",
                                          (self.args.name, env))
                continue
            else:
                data['relative_path'] = '/%s/%s/' % (env, self.args.name)
                data['id'] = '-'.join([self.args.name, env])
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    juicer.utils.Log.log_info("created repo `%s` in %s",
                                              (self.args.name, env))
                else:
                    _r.raise_for_status()

    def create_user(self, query='/users/'):
        """
        Create user in specified environments
        """
        data = {'login': self.args.login,
                'password': self.args.password,
                'name': self.args.name}

        juicer.utils.Log.log_debug("Create User: %s ('%s')", self.args.login, \
                self.args.name)

        for env in self.args.envs:
            if juicer.utils.user_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` already exists in %s... skipping!",
                                          (self.args.login, env))
                continue
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    juicer.utils.Log.log_info("created user `%s` with login `%s` in %s",
                                              (self.args.name, self.args.login, env))
                else:
                    _r.raise_for_status()

    def delete_repo(self, query='/repositories/'):
        """
        Delete repo in specified environments
        """
        juicer.utils.Log.log_debug("Delete Repo: %s", self.args.name)

        for env in self.args.envs:
            if not juicer.utils.repo_exists_p(self.args, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` doesn't exist in %s... skipping!",
                                           (self.args.name, env))
                continue
            else:
                url = "%s%s-%s/" % (query, self.args.name, env)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_ACCEPTED:
                    juicer.utils.Log.log_info("deleted repo `%s` in %s",
                                              (self.args.name, env))
                else:
                    _r.raise_for_status()

    def delete_user(self, query='/users/'):
        """
        Delete user in specified environments
        """
        juicer.utils.Log.log_debug("Delete User: %s", self.args.login)

        for env in self.args.envs:
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_OK:
                    juicer.utils.Log.log_info("deleted user `%s` in %s",
                                              (self.args.login, env))
                else:
                    _r.raise_for_status()

    def list_repos(self, query='/repositories/'):
        """
        List repositories in specified environments
        """
        juicer.utils.Log.log_debug(
                "List Repos In: %s", ", ".join(self.args.envs))

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for repo in juicer.utils.load_json_str(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        juicer.utils.Log.log_info("\t" + repo['name'])
            else:
                _r.raise_for_status()

    def role_add(self, query='/roles/'):
        data = {'username': self.args.login}
        juicer.utils.Log.log_debug(
                "Add Role '%s' to '%s'", self.args.role, self.args.login)

        for env in self.args.envs:
            if not juicer.utils.role_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("role `%s` doesn't exist in %s... skipping!",
                                          (self.args.role, env))
                continue
            elif not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (self.args.login, env))
            else:
                url = "%s%s/add/" % (query, self.args.role)
                _r = self.connectors[env].post(url, data)
                if _r.status_code == Constants.PULP_POST_OK:
                    juicer.utils.Log.log_info("added user `%s` to role `%s` in %s",
                                              (self.args.login, self.args.role, env))
                else:
                    _r.raise_for_status()

    def show_repo(self, query='/repositories/'):
        """
        Show repositories in specified environments
        """
        juicer.utils.Log.log_debug("Show Repo: %s", self.args.name)

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            url = "%s%s-%s/" % (query, self.args.name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == Constants.PULP_GET_OK:
                juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
            else:
                _r.raise_for_status()

    def show_user(self, query='/users/'):
        """
        Show user in specified environments
        """
        juicer.utils.Log.log_debug("Show User: %s", self.args.login)

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (self.args.login, env))
                continue
            else:
                url = "%s%s/" % (query, self.args.login)
                _r = self.connectors[env].get(url)
                if _r.status_code == Constants.PULP_GET_OK:
                    juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
                else:
                    _r.raise_for_status()

    def list_roles(self, query='/roles/'):
        """
        List roles in specified environments
        """
        juicer.utils.Log.log_debug("List Roles %s", ", ".join(self.args.envs))

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
            else:
                _r.raise_for_status()

    def update_user(self, query='/users/'):
        """
        Update user information
        """
        juicer.utils.Log.log_debug(
                "Update user information %s" % (self.args.login))

        data = {'login': self.args.login,
                'name': self.args.name,
                'password': self.args.password}

        query = "%s%s/" % (query, self.args.login)

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            if not juicer.utils.user_exists_p(self.args, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` does not exist in %s... skipping!",
                                          (self.args.login, env))
                continue
            else:
                _r = self.connectors[env].put(query, data)
                if _r.status_code == Constants.PULP_PUT_OK:
                    juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
                else:
                    _r.raise_for_status()
