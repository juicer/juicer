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

from juicer.admin.JuicerAdmin import JuicerAdmin as ja


def create_repo(args):
    pulp = ja(args)
    pulp.create_repo(args.arch, args.name, args.feed, args.envs, type=args.type)


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
    pulp.show_repo(args.name, args.envs)


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
