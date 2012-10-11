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
from juicer.common.Errors import *
import juicer.admin
import juicer.utils
import juicer.utils.Log
import re


class JuicerAdmin(object):
    def __init__(self, args):
        self.args = args

        (self.connectors, self._defaults) = juicer.utils.get_login_info()

        if 'envs' in self.args:
            for env in self.args.envs:
                try:
                    self.connectors[env].get()
                except KeyError:
                    juicer.utils.Log.log_error("%s is not a server configured in juicer.conf" % env)
                    juicer.utils.Log.log_debug("Exiting...")
                    exit(1)

    def create_repo(self, arch=None, name=None, feed=None, envs=None, type=None, query='/repositories/'):
        """
        `arch` - Architecture of repository content
        `name` - Name of repository to create
        `feed` - Repo URL to feed from
        `type` - Repository type (yum, file)

        Create repository in specified environments
        """
        name = name.lower()

        data = {'name': name,
                'arch': arch}

        if feed:
            data['feed'] = feed

        if type:
            data['content_types'] = type

        juicer.utils.Log.log_debug("Create Repo: %s", name)

        for env in envs:
            if juicer.utils.repo_exists_p(name, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` already exists in %s... skipping!",
                                          (name, env))
                continue
            else:
                data['relative_path'] = '/%s/%s/' % (env, name)
                data['id'] = '-'.join([name, env])
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    juicer.utils.Log.log_info("created repo `%s` in %s", name, env)
                else:
                    _r.raise_for_status()
        return True

    def create_user(self, login=None, password=None, name=None, envs=None, query='/users/'):
        """
        `login` - Login or username for user
        `password` - Plain text password for user
        `name` - Full name of user

        Create user in specified environments
        """
        login = login.lower()

        data = {'login': login,
                'password': password,
                'name': name}

        juicer.utils.Log.log_debug("Create User: %s ('%s')", login, name)

        for env in envs:
            if juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` already exists in %s... skipping!",
                                          (login, env))
                continue
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    juicer.utils.Log.log_info("created user `%s` with login `%s` in %s",
                                              (name, login, env))
                else:
                    _r.raise_for_status()
        return True

    def delete_repo(self, name=None, envs=None, query='/repositories/'):
        """
        `name` - Name of repository to delete

        Delete repo in specified environments
        """
        juicer.utils.Log.log_debug("Delete Repo: %s", self.args.name)

        for env in self.args.envs:
            if not juicer.utils.repo_exists_p(name, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` doesn't exist in %s... skipping!",
                                           (name, env))
                continue
            else:
                url = "%s%s-%s/" % (query, name, env)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_ACCEPTED:
                    juicer.utils.Log.log_info("deleted repo `%s` in %s",
                                              (name, env))
                else:
                    _r.raise_for_status()
        return True

    def delete_user(self, login=None, envs=None, query='/users/'):
        """
        `login` - Login or username of user to delete

        Delete user in specified environments
        """
        juicer.utils.Log.log_debug("Delete User: %s", login)

        for env in envs:
            if not juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (login, env))
                continue
            else:
                url = "%s%s/" % (query, login)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_OK:
                    juicer.utils.Log.log_info("deleted user `%s` in %s",
                                              (login, env))
                else:
                    _r.raise_for_status()
        return True

    def list_repos(self, envs=None, query='/repositories/'):
        """
        List repositories in specified environments
        """
        juicer.utils.Log.log_debug(
                "List Repos In: %s", ", ".join(envs))

        for env in envs:
            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for repo in juicer.utils.load_json_str(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        juicer.utils.Log.log_info("\t" + repo['name'])
            else:
                _r.raise_for_status()
        return True

    def role_add(self, role=None, login=None, envs=None, query='/roles/'):
        """
        `login` - Login or username of user to add to `role`
        `role` - Role to add user to

        Add user to role
        """
        data = {'username': self.args.login}
        juicer.utils.Log.log_debug(
                "Add Role '%s' to '%s'", role, login)

        for env in self.args.envs:
            if not juicer.utils.role_exists_p(role, self.connectors[env]):
                juicer.utils.Log.log_info("role `%s` doesn't exist in %s... skipping!",
                                          (role, env))
                continue
            elif not juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (login, env))
            else:
                url = "%s%s/add/" % (query, role)
                _r = self.connectors[env].post(url, data)
                if _r.status_code == Constants.PULP_POST_OK:
                    juicer.utils.Log.log_info("added user `%s` to role `%s` in %s",
                                              (login, role, env))
                else:
                    _r.raise_for_status()
        return True

    def show_repo(self, name=None, envs=None, query='/repositories/'):
        """
        `name` - Name of repository to show

        Show repositories in specified environments
        """
        juicer.utils.Log.log_debug("Show Repo: %s", name)

        for env in envs:
            juicer.utils.Log.log_info("%s:", env)
            url = "%s%s-%s/" % (query, name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == Constants.PULP_GET_OK:
                juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
            else:
                if _r.status_code == Constants.PULP_GET_NOT_FOUND:
                    juicer.utils.Log.log_error("repo '%s' was not found" % name)
                    exit(1)
                else:
                    _r.raise_for_status()
        return True

    def show_user(self, login=None, envs=None, query='/users/'):
        """
        `login` - Login or username of user

        Show user in specified environments
        """
        juicer.utils.Log.log_debug("Show User: %s", login)

        for env in self.args.envs:
            juicer.utils.Log.log_info("%s:", env)
            if not juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (login, env))
                continue
            else:
                url = "%s%s/" % (query, login)
                _r = self.connectors[env].get(url)
                if _r.status_code == Constants.PULP_GET_OK:
                    juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
                else:
                    _r.raise_for_status()
        return True

    def list_roles(self, envs=None, query='/roles/'):
        """
        List roles in specified environments
        """
        juicer.utils.Log.log_debug("List Roles %s", ", ".join(envs))

        for env in envs:
            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
            else:
                _r.raise_for_status()
        return True

    def update_user(self, login=None, name=None, password=None, envs=None, query='/users/'):
        """
        `login` - Login or username of user to update
        `name` - Updated full name of user
        `password` - Updated plain text password for user

        Update user information
        """
        juicer.utils.Log.log_debug("Update user information %s" % login)

        login = login.lower()

        data = {'login': login,
                'name': name,
                'password': password}

        query = "%s%s/" % (query, login)

        for env in envs:
            juicer.utils.Log.log_info("%s:", env)
            if not juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` does not exist in %s... skipping!",
                                          (login, env))
                continue
            else:
                _r = self.connectors[env].put(query, data)
                if _r.status_code == Constants.PULP_PUT_OK:
                    juicer.utils.Log.log_info(juicer.utils.load_json_str(_r.content))
                else:
                    _r.raise_for_status()
        return True

    def setup(self, envs=None, query='/repositories/'):
        """
        performs initial setup of pulp server(s) to work with juicer
        """
        if not envs:
            envs = self._defaults['environments']

        self.create_repo(name='carts', arch='noarch', envs=envs, type='file')
