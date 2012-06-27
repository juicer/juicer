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
from pprint import pprint as pp

def create_repo(args):
    pulp = ja(args)
    pp(pulp.create_repo())

def create_user(args):
    pulp = ja(args)
    pp(pulp.create_user())

def list_repos(args):
    pulp = ja(args)
    pp(pulp.list_repos())

def show_repo(args):
    pulp = ja(args)
    pp(pulp.show_repo())

def show_user(args):
    pulp = ja(args)
    pp(pulp.show_user())

def delete_repo(args):
    pulp = ja(args)
    pp(pulp.delete_repo())

def delete_user(args):
    pulp = ja(args)
    pp(pulp.delete_user())

def role_add(args):
    pulp = ja(args)
    pp(pulp.role_add())

def list_roles(args):
    pulp = ja(args)
    pp(pulp.list_roles())
