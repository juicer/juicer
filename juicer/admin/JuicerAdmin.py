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
from juicer.common.Repo import JuicerRepo, PulpRepo
import juicer.admin
import juicer.utils
import juicer.utils.Log
import juicer.utils.ValidateRepoDef
import juicer.admin.ThreaddedQuery
from juicer.utils.ProgressBar import ProgressBar as JuiceBar
import re
from multiprocessing.pool import ThreadPool
import multiprocessing
import progressbar


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

    def create_repo(self, repo_name=None, feed=None, envs=[], checksum_type="sha256", query='/repositories/'):
        """
        `repo_name` - Name of repository to create
        `feed` - Repo URL to feed from
        `checksum_type` - Used for generating meta-data

        Create repository in specified environments, associate the
        yum_distributor with it and publish the repo
        """

        data = {'display_name': repo_name,
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
                    imp_data = {
                        'importer_id': 'yum_importer',
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
        all_repos = [JuicerRepo(repo['name'], repo_def=repo) for repo in repo_defs]

        # Detailed information on all existing repos
        existing_repos = {}
        repo_pool = ThreadPool()

        # Parallelize getting the repo lists
        env_results = [repo_pool.apply_async(self.list_repos, tuple(), kwds={'envs': [er]}, callback=existing_repos.update) for er in all_envs]
        repo_pool.close()

        for result_async in env_results:
            result_async.wait()

        repo_pool.join()

        for repo in all_repos:
            # 'env' is all environments if: 'env' is not defined; 'env' is an empty list
            current_env = repo.get('env', [])
            if current_env == []:
                juicer.utils.Log.log_debug("Setting 'env' to all_envs for repo: %s" % repo['name'])
                repo['env'] = all_envs

        #  Assemble a set of all specified environments.
        defined_envs = juicer.utils.unique_repo_def_envs(all_repos)
        juicer.utils.Log.log_notice("Discovered environments: %s" % ", ".join(list(defined_envs)))

        widgets = [
            "Importing: ",
            progressbar.Percentage(),
            " ",
            "(",
            progressbar.SimpleProgress(),
            ") ",
            progressbar.ETA()
        ]
        progress_bar = JuiceBar(len(all_repos), widgets)
        repos_processed = juicer.admin.ThreaddedQuery.LookupObject()
        repos_processed.processed = 0
        # sort out new vs. existing
        # Break these into batches we can process at once
        for chunks in juicer.utils.chunks(all_repos, multiprocessing.cpu_count() - 1):
            crud_pool = ThreadPool()
            crud_args = (all_repos, all_envs, existing_repos, self, repo_objects_create, repo_objects_update, repos_processed, progress_bar)
            calculate_results = [crud_pool.apply_async(juicer.admin.ThreaddedQuery.calculate_create_and_update,
                                                       crud_args,
                                                       kwds={'repo': repo},
                                                       callback=juicer.admin.ThreaddedQuery.crud_progress_updater)
                                 for repo in chunks]
            crud_pool.close()
            to_process = len(calculate_results)
            juicer.utils.Log.log_debug("And we started the pool; items: %s" % len(calculate_results))
            while to_process > 0:
                for thingy in calculate_results:
                    thingy.wait(0.5)
                    if thingy.ready():
                        to_process -= 1
            crud_pool.join()

        juicer.utils.Log.log_debug("And we joined all threads")
        """repo_objects_update looks like this:

        {'environment': [repo_update_spec, ...]}

        repo_update_spec :: [env, repo_diff_spec, pulp_repo]

        env :: environment to apply diff to

        repo_diff_spec :: {
            'distributor': {'distributor_config': {PARAMETERS_TO_UPDATE: VALUES}},
            'importer': {'importer_config': {PARAMETERS_TO_UPDATE: VALUES}
            }
        }

        pulp_repo :: Json serialization of a repo as returned from pulp (or juicer-admin repo show --json)
        """
        return (repo_objects_create, repo_objects_update)

    def _update_repo(self, juicer_repo, pulp_repo, env, repo_diff, query='/repositories/'):
        """
        `from_file` - JSON file of repo definitions
        `noop` - Boolean, if true don't actually create/update repos, just show what would have happened

        https://pulp-dev-guide.readthedocs.org/en/pulp-2.3/integration/rest-api/repo/cud.html#update-a-distributor-associated-with-a-repository
        https://pulp-dev-guide.readthedocs.org/en/pulp-2.3/integration/rest-api/repo/cud.html#update-an-importer-associated-with-a-repository

        Distributor update:
        Method: PUT
        Path: /pulp/api/v2/repositories/<repo_id>/distributors/<distributor_id>/

        Importer update:
        Method: PUT
        Path: /pulp/api/v2/repositories/<repo_id>/importers/<importer_id>/
        """
        repo_id = "%s-%s" % (juicer_repo['name'], env)
        distributor_id = "yum_distributor"
        importer_id = "yum_importer"
        distributor_diff = repo_diff.diff()['distributor']
        importer_diff = repo_diff.diff()['importer']

        distributor_query = query + "%s/distributors/%s/" % (repo_id, distributor_id)
        importer_query = query + "%s/importers/%s/" % (repo_id, importer_id)

        ##############################################################
        # Importer update
        _r = self.connectors[env].put(distributor_query, distributor_diff)
        if _r.status_code == Constants.PULP_PUT_OK:
            juicer.utils.Log.log_notice("Update request accepted for %s", repo_id)
        elif _r.status_code == Constants.PULP_PUT_CONFLICT:
            juicer.utils.Log.log_debug(str(_r.content))
        elif _r.status_code == Constants.PULP_PUT_NOT_FOUND:
            juicer.utils.Log.log_debug(str(_r.content))
        else:
            _r.raise_for_status()

        ##############################################################
        # Distributor update
        _r = self.connectors[env].put(importer_query, importer_diff)
        if _r.status_code == Constants.PULP_PUT_OK:
            juicer.utils.Log.log_notice("Update request accepted for %s", repo_id)
        elif _r.status_code == Constants.PULP_PUT_CONFLICT:
            juicer.utils.Log.log_debug(str(_r.content))
        elif _r.status_code == Constants.PULP_PUT_NOT_FOUND:
            juicer.utils.Log.log_debug(str(_r.content))
        else:
            _r.raise_for_status()

        return True

    def export_repos(self, envs=[]):
        """Dump JuicerRepo() objects for all repos in all environments.

        Note that this has undefined results should a repo exist with
        different configurations in different environments.
        """
        all_envs = envs
        juicer.utils.Log.log_notice("Only exporting repos in environment(s): %s", ", ".join(all_envs))
        all_pulp_repo_names = self.list_repos(envs=all_envs)
        all_pulp_repo_names_uniqued = set()
        num_repos = 0

        # Track name of all processed repos. Update when we've found
        # all environments a PulpRepo lives in.
        repos_processed = []

        for env, repos in all_pulp_repo_names.iteritems():
            juicer.utils.Log.log_debug("Uniqued environment: %s with %s repos", env, int(len(repos)))
            all_pulp_repo_names_uniqued.update(set(repos))

        num_repos += len(all_pulp_repo_names_uniqued)

        widgets = [
            "Exporting: ",
            progressbar.Percentage(),
            " ",
            "(",
            progressbar.SimpleProgress(),
            ") ",
            progressbar.ETA()
        ]
        progress_bar = JuiceBar(num_repos, widgets)

        # Hacky way to get around not easily being able to pass
        # multiple arguments to a function in a multiprocessing pool
        lookup_objects = []

        for repo in all_pulp_repo_names_uniqued:
            lookup_args = juicer.admin.ThreaddedQuery.LookupObject()
            setattr(lookup_args, 'progress_bar', progress_bar)
            setattr(lookup_args, 'all_pulp_repo_names', all_pulp_repo_names)
            setattr(lookup_args, 'all_envs', all_envs)
            setattr(lookup_args, 'ja', self)
            setattr(lookup_args, 'pulp_repo', repo)
            setattr(lookup_args, 'repos_processed', repos_processed)
            lookup_objects.append(lookup_args)

        # TODO: Add the serial/concurrent logic here

        try:
            # Make our thread pool
            p = ThreadPool()
            # Get an AsyncResult object
            r = p.map_async(juicer.admin.ThreaddedQuery.concurrent_pulp_lookup, lookup_objects)
            # TODO: We should probably use p.apply_async here to avoid the crappy lookup_objects hack

            while not r.ready():
                r.wait(1)
        except KeyboardInterrupt:
            juicer.utils.Log.log_error("User pressed ^C during repo export")
            juicer.utils.Log.log_error("Terminating %s worker threads and then exiting", len(p._pool))
            # Prevents any more tasks from being submitted to the
            # pool. Once all the tasks have been completed the worker
            # threads will exit.
            #p.close()
            p.terminate()
            p.join()

        # XXX: End serial/concurrent logic

        progress_bar.finish()
        juicer_repos = [pr.to_juicer_repo() for pr in repos_processed]
        return sorted(juicer_repos, key=lambda d: d['name'].lower())

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
                    repo_object = PulpRepo(repo_name, env, repo_def=repo)
                    repo_objects[env].append(repo_object)
                else:
                    if _r.status_code == Constants.PULP_GET_NOT_FOUND:
                        juicer.utils.Log.log_warn("could not find repo '%s' in %s" % (repo_name, env))
                    else:
                        _r.raise_for_status()
        for k, v in repo_objects.iteritems():
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

        data = {'delta': {}}

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
