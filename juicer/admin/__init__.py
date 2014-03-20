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

from juicer.admin.JuicerAdmin import JuicerAdmin as ja
import juicer.utils
import sys


def create_repo(args):
    pulp = ja(args)
    pulp.create_repo(args.name, args.feed, args.envs, args.checksum_type)


def export_repo(args):
    pulp = ja(args)
    export_list = pulp.export_repos(args.envs)
    fmt_args = {}
    fmt_args['cls'] = juicer.common.Repo.RepoEncoder
    if args.pretty:
        fmt_args['indent'] = 4

    if args.out == '-':
        writer = sys.stdout
    else:
        writer = open(args.out, 'w')

    export_str = juicer.utils.create_json_str(export_list, **fmt_args)
    writer.write(export_str)
    writer.flush()


def import_repo(args):
    pulp = ja(args)
    # Get our TODO specs from juicer-admin
    (to_create, to_update) = pulp.import_repo(args.from_file, args.noop)

    if args.noop:
        num_to_create = 0
        num_to_update = 0
        if to_create:
            juicer.utils.Log.log_info("NOOP: Would have created repos with definitions:")
            juicer.utils.Log.log_info("%s", juicer.utils.create_json_str(to_create, indent=4, cls=juicer.common.Repo.RepoEncoder))
            for repo in to_create:
                num_to_create += len(repo['missing_in_env'])

        for env, repos in to_update.iteritems():
            for repo in repos:
                noop_msg = None
                debug_msg = False
                repo_diff_specs = repo['reality_check_in_env']
                for diff_spec in repo_diff_specs:
                    # [0] = env, [1] = RepoDiff, [2] = PulpRepo
                    if diff_spec[0] == env:
                        this_env_diff_spec = diff_spec
                        # "{'distributor': {'distributor_config': {}}, 'importer': {'importer_config': {}}}"
                        repo_diff = diff_spec[1]
                        # Does the diff contain anything?
                        whole_diff = {}
                        rdist = repo_diff.diff()['distributor']['distributor_config']
                        rimp = repo_diff.diff()['importer']['importer_config']

                        if not rdist == {}:
                            whole_diff['distributor'] = rdist
                            debug_msg = True
                        if not rimp == {}:
                            whole_diff['importer'] = rimp
                            debug_msg = True
                        if debug_msg:
                            noop_msg = "    %s" % juicer.utils.create_json_str(whole_diff, indent=4, cls=juicer.common.Repo.RepoEncoder)

                if debug_msg:
                    juicer.utils.Log.log_info("NOOP: Would have updated %s-%s with:", repo['name'], env)
                    juicer.utils.Log.log_info(noop_msg)
                    num_to_update += 1

        juicer.utils.exit_with_code(num_to_create + num_to_update)

    else:
        for repo in to_create:
            pulp.create_repo(repo_name=repo['name'],
                             feed=repo['feed'],
                             envs=repo['missing_in_env'],
                             checksum_type=repo['checksum_type'])

        for env, repos in to_update.iteritems():
            for repo in repos:
                repo_diff_specs = repo['reality_check_in_env']
                for diff_spec in repo_diff_specs:
                    if diff_spec[0] == env:
                        repo_diff = diff_spec[1]
                        if repo_diff.diff()['distributor']['distributor_config'] or repo_diff.diff()['importer']['importer_config']:
                            try:
                                # TODO: This could benefit from some concurrency, like how export_repo goes...
                                pulp._update_repo(repo, diff_spec[2], env, diff_spec[1])
                            except Exception:
                                juicer.utils.Log.log_error("Unable to update %s-%s", repo['name'], env)
                            else:
                                juicer.utils.Log.log_info("Updated %s-%s with:", repo['name'], env)
                                debug_msg = "    %s\n" % juicer.utils.create_json_str(repo_diff.diff(), indent=4, cls=juicer.common.Repo.RepoEncoder)
                                juicer.utils.Log.log_info(debug_msg)


def create_user(args):
    pulp = ja(args)
    pulp.create_user(args.login, args.password, args.name, args.envs)


def list_repos(args):
    pulp = ja(args)
    repo_lists = pulp.list_repos(args.envs)
    if args.json:
        print juicer.utils.create_json_str(repo_lists, indent=4)
    else:
        for env, repos in repo_lists.iteritems():
            print "%s(%d): %s" % (env, len(repos), ' '.join(repos))


def sync_repo(args):
    pulp = ja(args)
    pulp.sync_repo(args.name, args.envs)


def show_repo(args):
    pulp = ja(args)
    repo_objects = pulp.show_repo(args.name, args.envs)

    if args.json:
        # JSON output requested
        print juicer.utils.create_json_str(repo_objects, indent=4,
                                           cls=juicer.common.Repo.RepoEncoder)
    else:
        found_repos = 0
        for env, repos in repo_objects.iteritems():
            found_repos += len(repos)
        if found_repos == 0:
            print "Could not locate repo(s) in any environment"
            return False

        # Human readable table-style output by default
        rows = [['Repo', 'Env', 'RPMs', 'SRPMs', 'Checksum', 'Feed']]
        # If feeds are set, things can get messy. Lets make this wider
        # if anybody has a feed
        found_feed = False
        for env, repos in repo_objects.iteritems():
            # 'repos' contains a list of hashes
            for repo in repos:
                # each hash represents a repo
                repo_name = repo['name']
                repo_rpm_count = repo['rpm_count']
                repo_srpm_count = repo['srpm_count']
                repo_checksum = repo['checksum_type']
                repo_feed = repo['feed']
                rows.append([repo_name, env, repo_rpm_count, repo_srpm_count, repo_checksum, str(repo_feed)])
                if not repo_feed is None:
                    juicer.utils.Log.log_debug("Found a repo feed. Making the table wider.")
                    found_feed = True

        if found_feed:
            print juicer.utils.table(rows, columns=0)
        else:
            print juicer.utils.table(rows)


def show_user(args):
    pulp = ja(args)
    pulp.show_user(args.login, args.envs)


def delete_repo(args):
    pulp = ja(args)
    pulp.delete_repo(args.name, args.envs)


def delete_user(args):
    pulp = ja(args)
    pulp.delete_user(args.login, args.envs)


def role_add(args):
    pulp = ja(args)
    pulp.role_add(args.role, args.login, args.envs)


def list_roles(args):
    pulp = ja(args)
    pulp.list_roles(args.envs)


def update_user(args):
    pulp = ja(args)
    pulp.update_user(args.login, args.name, args.password, args.envs)


def setup(args):
    pulp = ja(args)
    pulp.setup()


def list_users(args):
    pulp = ja(args)
    pulp.list_users(args.envs)
