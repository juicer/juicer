# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2012-2014, Red Hat, Inc.
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
from juicer.common.Repo import Repo
import juicer.admin
import juicer.utils
import juicer.utils.Log
import juicer.utils.ValidateRepoDef
import re
import json


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
        `from_file` - JSON file of repo definitions
        `noop` - Boolean, if true don't actually create/update repos, just show what would have happened

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

    def import_repo(self, from_file, noop=False, query='/repositories/'):
        """
        `from_file` - JSON file of repo definitions
        `noop` - Boolean, if true don't actually create/update repos, just show what would have happened
        """
        try:
            repo_defs = juicer.utils.ValidateRepoDef.validate_document(from_file)
        except JuicerRepoDefError, e:
            juicer.utils.Log.log_error("Could not load repo defs from %s:" % from_file)
            raise e
        else:
            juicer.utils.Log.log_debug("Loaded and validated repo defs from %s" % from_file)

        # All our known envs, for cases where no value is supplied for 'env'
        all_envs = juicer.utils.get_environments()

        # Repos to create/update, sorted by environment.
        repo_objects_create = []
        repo_objects_update = {}
        for env in all_envs:
            repo_objects_update[env] = []

        # All repo defs as Repo objects
        all_repos = [juicer.common.Repo.Repo(repo['name'], repo_def=repo) for repo in repo_defs]

        # Detailed information on all existing repos
        #
        # TODO: Optimize this so we only call to pulp for environments
        # we KNOW we need to operate in. Determine this by evaluating
        # the 'env' property of each repo def.
        if not noop:
            juicer.utils.Log.log_notice("Loading information on all existing repos (this could take a while)")
            #existing_repos = self.list_repos(envs=all_envs)

        # Use a cache now to speed up testing
        juicer.utils.Log.log_info("BE AWARE: Currently reading repo list from local cache")
        existing_repos = juicer.utils.read_json_document('/tmp/repo_list.json')


        for repo in all_repos:
            # 'env' is all environments if: 'env' is not defined; 'env' is an empty list
            current_env = repo.get('env', [])
            if current_env == []:
                juicer.utils.Log.log_debug("Setting 'env' to all_envs for repo: %s" % repo['name'])
                repo['env'] = all_envs

        #  Assemble a set of all specified environments.
        defined_envs = juicer.utils.unique_repo_def_envs(all_repos)
        juicer.utils.Log.log_notice("Discovered environments: %s" % ", ".join(list(defined_envs)))

        # sort out new vs. existing
        for repo in all_repos:
            # Does the repo refer to environments in our juicer.conf file?
            if juicer.utils.repo_in_defined_envs(repo, all_envs):
                repo['reality_check_in_env'] = []
                repo['missing_in_env'] = []
                for env in repo['env']:
                    if juicer.utils.repo_exists_in_repo_list(repo, existing_repos[env]):
                        # Does the repo def match what exists already?
                        if juicer.utils.repo_def_matches_reality(repo, env):
                            juicer.utils.Log.log_notice("Repo %s already exists and reality matches the definition", repo['name'])
                        else:
                            juicer.utils.Log.log_notice("Repo %s already exists, but reality does not the definition", repo['name'])
                            repo['reality_check_in_env'].append(env)
                    else:
                        # The repo does not exist yet in reality
                        juicer.utils.Log.log_notice("Need to create %s in %s", repo['name'], env)
                        repo['missing_in_env'].append(env)

                # Do we need to create the repo anywhere?
                if repo['missing_in_env']:
                    repo_objects_create.append(repo)

                # We we need to update the repo anywhere?
                if repo['reality_check_in_env']:
                    for env in repo['reality_check_in_env']:
                        repo_objects_update[env].append(repo)


        return (repo_objects_create, repo_objects_update)

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

        repo_lists = {}
        for env in envs:
            repo_lists[env] = []

        for env in envs:
            _r = self.connectors[env].get(query)
            if _r.status_code == Constants.PULP_GET_OK:
                for repo in juicer.utils.load_json_str(_r.content):
                    if re.match(".*-{0}$".format(env), repo['id']):
                        repo_lists[env].append(repo['display_name'])
            else:
                _r.raise_for_status()
        return repo_lists

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

    def show_repo(self, repo_names=[], envs=[], query='/repositories/'):
        """
        `repo_names` - Name of repository(s) to show

        Show repositories in specified environments
        """
        juicer.utils.Log.log_debug("Show Repo(s): %s", str(repo_names))

        repo_objects = {}
        for env in envs:
            repo_objects[env] = []

        for env in envs:
            juicer.utils.Log.log_debug("scanning environment: %s", env)
            for repo_name in repo_names:
                juicer.utils.Log.log_debug("looking for repo: %s", repo_name)
                url = "%s%s-%s/?details=true" % (query, repo_name, env)
                _r = self.connectors[env].get(url)
                if _r.status_code == Constants.PULP_GET_OK:
                    juicer.utils.Log.log_debug("found repo: %s", repo_name)
                    repo = juicer.utils.load_json_str(_r.content)
                    repo_object = Repo(repo_name, env, pulp_def=repo)
                    repo_objects[env].append(repo_object)
                else:
                    if _r.status_code == Constants.PULP_GET_NOT_FOUND:
                        juicer.utils.Log.log_warn("could not find repo '%s' in %s" % (repo_name, env))
                    else:
                        _r.raise_for_status()
        for k,v in repo_objects.iteritems():
            juicer.utils.Log.log_debug("environment %s: found %d repos" % (k, len(v)))
        return repo_objects

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
