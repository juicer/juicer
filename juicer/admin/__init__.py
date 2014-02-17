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

from juicer.admin.JuicerAdmin import JuicerAdmin as ja
import juicer.utils

def create_repo(args):
    pulp = ja(args)
    pulp.create_repo(args.arch, args.name, args.feed, args.envs, args.checksum_type, args.json_defs, args.noop)


def create_user(args):
    pulp = ja(args)
    pulp.create_user(args.login, args.password, args.name, args.envs)


def list_repos(args):
    pulp = ja(args)
    pulp.list_repos(args.envs)


def sync_repo(args):
    pulp = ja(args)
    pulp.sync_repo(args.name, args.envs)


def show_repo(args):
    pulp = ja(args)
    repo_desc = pulp.show_repo(args.name, args.envs)
    if args.json:
        # JSON output requested
        print juicer.utils.create_json_str(repo_desc, indent=4)
    else:
        # Human readable table-style output by default
        rows = [['Repo', 'Env', 'RPMs', 'SRPMs', 'Checksum']]
        for env,repos in repo_desc.iteritems():
            # print juicer.utils.header(env.upper())
            # 'repos' contains a list of hashes
            for repo in repos:
                # each hash represents a repo
                repo_name = repo['display_name']
                repo_rpm_count = repo['content_unit_counts']['rpm']
                repo_srpm_count = repo['content_unit_counts']['srpm']
                repo_checksum = repo['scratchpad']['checksum_type']
                rows.append([repo_name, env, repo_rpm_count, repo_srpm_count, repo_checksum])

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
