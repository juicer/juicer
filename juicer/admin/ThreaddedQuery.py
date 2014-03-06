# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2014, Red Hat, Inc.
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

import juicer.admin
import juicer.utils
import juicer.utils.Log
import juicer.utils.ValidateRepoDef
import threading
import multiprocessing

JUICER_CPU_COUNT = multiprocessing.cpu_count()

PROCESSED_LOCK = threading.Lock()
PROGRESS_LOCK = threading.Lock()

CREATE_LOCK = threading.Lock()
UPDATE_LOCK = threading.Lock()

CRUD_COUNT_LOCK = threading.Lock()
CRUD_PROGRESS_LOCK = threading.Lock()


class LookupObject(object):
    def __init__(self):
        pass


def concurrent_pulp_lookup(lookup_object):
    juicer.utils.Log.log_debug("Processing stuff, whoooooooooooo: %s", lookup_object.pulp_repo)
    pulp_repo = lookup_object.pulp_repo
    all_envs = lookup_object.all_envs
    all_pulp_repo_names = lookup_object.all_pulp_repo_names
    ja = lookup_object.ja
    progress_bar = lookup_object.progress_bar
    repos_processed = lookup_object.repos_processed

    juicer.utils.Log.log_debug("Finding all environments %s lives in", pulp_repo)
    envs = [env for env in all_envs if pulp_repo in all_pulp_repo_names[env]]
    juicer.utils.Log.log_debug("%s exists in %s", pulp_repo, str(envs))
    # use the last environment in the list, as that is most
    # likely prod, which is most likely the desired state
    last_env = envs[-1]
    juicer.utils.Log.log_debug("The 'last_env' for %s is %s", pulp_repo, last_env)
    _pulp_repo = ja.show_repo([pulp_repo], envs=[last_env])[last_env][0]
    _pulp_repo['env'] = envs

    PROCESSED_LOCK.acquire()
    juicer.utils.Log.log_debug("PROCESSED_LIST: LOCKED by %s", pulp_repo)
    repos_processed.append(_pulp_repo)
    total_processed = len(repos_processed)
    juicer.utils.Log.log_debug("updated repos_processed list for %s", pulp_repo)
    PROCESSED_LOCK.release()
    juicer.utils.Log.log_debug("PROCESSED_LIST: RELEASED by %s", pulp_repo)

    PROGRESS_LOCK.acquire()
    juicer.utils.Log.log_debug("PROGRESS_BAR: LOCKED by %s", pulp_repo)
    progress_bar.update(total_processed)
    juicer.utils.Log.log_debug("Updated progress_bar for %s", pulp_repo)
    PROGRESS_LOCK.release()
    juicer.utils.Log.log_debug("PROGRESS_BAR: RELEASED by %s", pulp_repo)

    juicer.utils.Log.log_debug("Processed initial export step for %s", pulp_repo)
    return True


def calculate_create_and_update(all_repos, all_envs, existing_repos, ja, to_create, to_update, repos_processed, progress_bar, repo=None):
    juicer.utils.Log.log_debug("Calculating CRUD for %s", repo['name'])
    # Does the repo refer to environments in our juicer.conf file?
    if juicer.utils.repo_in_defined_envs(repo, all_envs):
        repo['reality_check_in_env'] = []
        repo['missing_in_env'] = []
        for env in repo['env']:
            if juicer.utils.repo_exists_in_repo_list(repo, existing_repos[env]):
                # Does the repo def match what exists already?
                pulp_repo = ja.show_repo(repo_names=[repo['name']], envs=[env])
                #juicer.utils.Log.log_debug(str(pulp_repo))
                repo_diff = juicer.utils.repo_def_matches_reality(repo, pulp_repo[env][0])
                if not repo_diff.diff()['distributor'] or repo_diff.diff()['importer']:
                    juicer.utils.Log.log_notice("Repo %s already exists in %s, but reality does not the definition", repo['name'], env)
                    # TODO: Need a better way to track this
                    # information. The repo_objects_create
                    # datastructure gets pretty messy and
                    # duplicates a lot of information.
                    repo['reality_check_in_env'].append((env, repo_diff, pulp_repo[env][0]))
                else:
                    juicer.utils.Log.log_notice("Repo %s already exists and is correct", repo['name'])
            else:
                # The repo does not exist yet in reality
                juicer.utils.Log.log_notice("Need to create %s in %s", repo['name'], env)
                repo['missing_in_env'].append(env)

        juicer.utils.Log.log_debug(threading.active_count())
        # Do we need to create the repo anywhere?
        if repo['missing_in_env']:
            CREATE_LOCK.acquire()
            to_create.append(repo)
            CREATE_LOCK.release()

        # We we need to update the repo anywhere?
        if repo['reality_check_in_env']:
            UPDATE_LOCK.acquire()
            for env, repo_diff, pulp_repo in repo['reality_check_in_env']:
                to_update[env].append(repo)
            UPDATE_LOCK.release()

    return (repos_processed, progress_bar)


def crud_progress_updater(input):
    (r, p) = input
    CRUD_COUNT_LOCK.acquire()
    r.processed += 1
    CRUD_COUNT_LOCK.release()
    CRUD_PROGRESS_LOCK.acquire()
    p.update(r.processed)
    CRUD_PROGRESS_LOCK.release()
