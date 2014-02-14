# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2012,2013, Red Hat, Inc.
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

    def create_repo(self, arch='noarch', repo_name=None, feed=None, envs=[], checksum_type="sha256", query='/repositories/'):
        """
        `arch` - Architecture of repository content
        `repo_name` - Name of repository to create
        `feed` - Repo URL to feed from
        `checksum_type` - Used for generating meta-data

        Create repository in specified environments, associate the
        yum_distributor with it and publish the repo
        """

        data = {'display_name': repo_name,
                'arch': arch,
                'notes': {
                    '_repo-type': 'rpm-repo',
                    }
                }
        juicer.utils.Log.log_debug("Create Repo: %s", repo_name)

        for env in envs:
            if juicer.utils.repo_exists_p(repo_name, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` already exists in %s... skipping!",
                                          (repo_name, env))
                continue
            else:
                data['relative_path'] = '/%s/%s/' % (env, repo_name)
                data['id'] = '-'.join([repo_name, env])

                _r = self.connectors[env].post(query, data)

                if _r.status_code == Constants.PULP_POST_CREATED:
                    imp_query = '/repositories/%s/importers/' % data['id']
                    imp_data = {'importer_id': 'yum_importer',
                            'importer_type_id': 'yum_importer',
                            'importer_config': {},
                            }

                    if feed:
                        imp_data['importer_config']['feed_url'] = feed

                    _r = self.connectors[env].post(imp_query, imp_data)

                    dist_query = '/repositories/%s/distributors/' % data['id']
                    dist_data = {'distributor_id': 'yum_distributor',
                            'distributor_type_id': 'yum_distributor',
                            'distributor_config': {
                                'relative_url': '/%s/%s/' % (env, repo_name),
                                'http': True,
                                'https': True,
                                'checksum_type': checksum_type
                                },
                            'auto_publish': True,
                            'relative_path': '/%s/%s/' % (env, repo_name)
                            }

                    _r = self.connectors[env].post(dist_query, dist_data)

                    if _r.status_code == Constants.PULP_POST_CREATED:
                        pub_query = '/repositories/%s/actions/publish/' % data['id']
                        pub_data = {'id': 'yum_distributor'}

                        _r = self.connectors[env].post(pub_query, pub_data)

                        if _r.status_code == Constants.PULP_POST_ACCEPTED:
                            juicer.utils.Log.log_info("created repo `%s` in %s", repo_name, env)
                    else:
                        _r.raise_for_status()
                else:
                    _r.raise_for_status()
        return True

    def create_user(self, login=None, password=None, user_name=None, envs=[], query='/users/'):
        """
        `login` - Login or username for user
        `password` - Plain text password for user
        `user_name` - Full name of user

        Create user in specified environments
        """
        login = login.lower()

        data = {'login': login,
                'password': password[0],
                'name': user_name}

        juicer.utils.Log.log_debug("Create User: %s ('%s')", login, user_name)

        for env in envs:
            if envs.index(env) != 0 and juicer.utils.env_same_host(env, envs[envs.index(env) - 1]):
                juicer.utils.Log.log_info("environment `%s` shares a host with environment `%s`... skipping!",
                                          (env, envs[envs.index(env) - 1]))
                continue
            elif juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` already exists in %s... skipping!",
                                          (login, env))
                continue
            else:
                _r = self.connectors[env].post(query, data)
                if _r.status_code == Constants.PULP_POST_CREATED:
                    juicer.utils.Log.log_info("created user `%s` with login `%s` in %s",
                                              (user_name, login, env))
                else:
                    _r.raise_for_status()
        return True

    def delete_repo(self, repo_name=None, envs=[], query='/repositories/'):
        """
        `repo_name` - Name of repository to delete

        Delete repo in specified environments
        """
        orphan_query = '/content/orphans/rpm/'
        juicer.utils.Log.log_debug("Delete Repo: %s", repo_name)

        for env in self.args.envs:
            if not juicer.utils.repo_exists_p(repo_name, self.connectors[env], env):
                juicer.utils.Log.log_info("repo `%s` doesn't exist in %s... skipping!",
                                           (repo_name, env))
                continue
            else:
                url = "%s%s-%s/" % (query, repo_name, env)
                _r = self.connectors[env].delete(url)
                if _r.status_code == Constants.PULP_DELETE_ACCEPTED:
                    juicer.utils.Log.log_info("deleted repo `%s` in %s",
                                              (repo_name, env))

                    # if delete was successful, delete orphaned rpms
                    _r = self.connectors[env].get(orphan_query)
                    if _r.status_code is Constants.PULP_GET_OK:
                        if len(juicer.utils.load_json_str(_r.content)) > 0:
                            __r = self.connectors[env].delete(orphan_query)
                            if __r.status_code is Constants.PULP_DELETE_ACCEPTED:
                                juicer.utils.Log.log_debug("deleted orphaned rpms in %s." % env)
                            else:
                                juicer.utils.Log.log_error("unable to delete orphaned rpms in %s. a %s error was returned", (env, __r.status_code))
                    else:
                        juicer.utils.Log.log_error("unable to get a list of orphaned rpms. encountered a %s error." % _r.status_code)
                else:
                    _r.raise_for_status()
        return True

    def delete_user(self, login=None, envs=[], query='/users/'):
        """
        `login` - Login or username of user to delete

        Delete user in specified environments
        """
        juicer.utils.Log.log_debug("Delete User: %s", login)

        for env in envs:
            if envs.index(env) != 0 and juicer.utils.env_same_host(env, envs[envs.index(env) - 1]):
                juicer.utils.Log.log_info("environment `%s` shares a host with environment `%s`... skipping!",
                                          (env, envs[envs.index(env) - 1]))
                continue
            elif not juicer.utils.user_exists_p(login, self.connectors[env]):
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

    def sync_repo(self, repo_name=None, envs=[], query='/repositories/'):
        """
        Sync repository in specified environments
        """
        juicer.utils.Log.log_debug(
               "Sync Repo %s In: %s" % (repo_name, ",".join(envs)))

        data = {
            'override_config': {
                'verify_checksum': 'true',
                'verify_size': 'true'
                },
            }

        for env in envs:
            url = "%s%s-%s/actions/sync/" % (query, repo_name, env)
            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].post(url, data)
            if _r.status_code == Constants.PULP_POST_ACCEPTED:
                juicer.utils.Log.log_info("`%s` sync scheduled" % repo_name)
            else:
                _r.raise_for_status()
        return True

    def list_repos(self, envs=[], query='/repositories/'):
        """
        List repositories in specified environments
        """
        juicer.utils.Log.log_debug(
                "List Repos In: %s", ", ".join(envs))

        count = 0

        for env in envs:
            count += 1

            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for repo in juicer.utils.load_json_str(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        juicer.utils.Log.log_info(repo['display_name'])

                if count < len(envs):
                    juicer.utils.Log.log_info("")
            else:
                _r.raise_for_status()
        return True

    def list_users(self, envs=[], query="/users/"):
        """
        List users in specified environments
        """
        juicer.utils.Log.log_debug(
                "List Users In: %s", ", ".join(envs))
        for env in envs:
            juicer.utils.Log.log_info("%s:" % (env))
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for user in juicer.utils.load_json_str(_r.content):
                    roles = user['roles']
                    if roles:
                        user_roles = ', '.join(roles)
                    else:
                        user_roles = "None"
                    juicer.utils.Log.log_info("\t%s - %s" % (user['login'], user_roles))
            else:
                _r.raise_for_status()
        return True

    def role_add(self, role=None, login=None, envs=[], query='/roles/'):
        """
        `login` - Login or username of user to add to `role`
        `role` - Role to add user to

        Add user to role
        """
        data = {'login': self.args.login}
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
                url = "%s%s/users/" % (query, role)
                _r = self.connectors[env].post(url, data)
                if _r.status_code == Constants.PULP_POST_OK:
                    juicer.utils.Log.log_info("added user `%s` to role `%s` in %s",
                                              (login, role, env))
                else:
                    _r.raise_for_status()
        return True

    def show_repo(self, repo_name=None, envs=[], query='/repositories/'):
        """
        `repo_name` - Name of repository to show

        Show repositories in specified environments
        """
        juicer.utils.Log.log_debug("Show Repo: %s", repo_name)

        # keep track of which iteration of environment we're in
        count = 0

        for env in envs:
            count += 1

            juicer.utils.Log.log_info("%s:", env)
            url = "%s%s-%s/" % (query, repo_name, env)
            _r = self.connectors[env].get(url)
            if _r.status_code == Constants.PULP_GET_OK:
                repo = juicer.utils.load_json_str(_r.content)

                juicer.utils.Log.log_info(repo['display_name'])
                try:
                    juicer.utils.Log.log_info("%s packages" % repo['content_unit_counts']['rpm'])
                except:
                    juicer.utils.Log.log_info("0 packages")

                if count < len(envs):
                    # just want a new line
                    juicer.utils.Log.log_info("")
            else:
                if _r.status_code == Constants.PULP_GET_NOT_FOUND:
                    raise JuicerPulpError("repo '%s' was not found" % repo_name)
                else:
                    _r.raise_for_status()
        return True

    def show_user(self, login=None, envs=[], query='/users/'):
        """
        `login` - Login or username of user

        Show user in specified environments
        """
        juicer.utils.Log.log_debug("Show User: %s", login)

        # keep track of which iteration of environment we're in
        count = 0

        for env in self.args.envs:
            count += 1

            juicer.utils.Log.log_info("%s:", env)
            if not juicer.utils.user_exists_p(login, self.connectors[env]):
                juicer.utils.Log.log_info("user `%s` doesn't exist in %s... skipping!",
                                          (login, env))
                continue
            else:
                url = "%s%s/" % (query, login)
                _r = self.connectors[env].get(url)
                if _r.status_code == Constants.PULP_GET_OK:
                    user = juicer.utils.load_json_str(_r.content)

                    juicer.utils.Log.log_info("Login: %s" % user['login'])
                    juicer.utils.Log.log_info("Name: %s" % user['name'])
                    juicer.utils.Log.log_info("Roles: %s" % ', '.join(user['roles']))

                    if count < len(envs):
                        # just want a new line
                        juicer.utils.Log.log_info("")
                else:
                    _r.raise_for_status()
        return True

    def list_roles(self, envs=[], query='/roles/'):
        """
        List roles in specified environments
        """
        juicer.utils.Log.log_debug("List Roles %s", ", ".join(envs))

        count = 0

        for env in envs:
            count += 1
            rcount = 0

            juicer.utils.Log.log_info("%s:", env)
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                roles = juicer.utils.load_json_str(_r.content)

                for role in roles:
                    rcount += 1

                    juicer.utils.Log.log_info("Name: %s" % role['display_name'])
                    juicer.utils.Log.log_info("Description: %s" % role['description'])
                    juicer.utils.Log.log_info("ID: %s" % role['id'])
                    juicer.utils.Log.log_info("Users: %s" % ', '.join(role['users']))

                    if rcount < len(roles):
                        # just want a new line
                        juicer.utils.Log.log_info("\n")

                if count < len(envs):
                    # just want a new line
                    juicer.utils.Log.log_info("\n")
            else:
                _r.raise_for_status()
        return True

    def update_user(self, login=None, user_name=None, password=None, envs=[], query='/users/'):
        """
        `login` - Login or username of user to update
        `user_name` - Updated full name of user
        `password` - Updated plain text password for user

        Update user information
        """
        juicer.utils.Log.log_debug("Update user information %s" % login)

        login = login.lower()

        data = { 'delta': {} }

        if not user_name and not password:
            raise JuicerError("Error: --name or --password must be present")

        if user_name:
            data['delta']['name'] = user_name

        if password:
            data['delta']['password'] = password[0]

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
                    juicer.utils.Log.log_info("user %s updated" %
                            juicer.utils.load_json_str(_r.content)['login'])
                else:
                    _r.raise_for_status()
        return True
