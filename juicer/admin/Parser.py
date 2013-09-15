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

import argparse
import juicer.admin
import juicer.utils
from juicer.utils.PromptAction import PromptAction


class Parser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Manage pulp')
        juicer.admin.parser = self.parser

        self._default_envs = juicer.utils.get_environments()

        self.parser.add_argument('-v', action='count', \
                                 default=1, \
                                 help='Increase the verbosity (up to 3x)')

        ##################################################################
        # Keep the different commands separate
        self.subparsers = self.parser.add_subparsers(title='Commands', \
           dest='command', \
           description='\'%(prog)s COMMAND -h\' for individual help topics')

        ##################################################################
        # Create the 'create_repo' sub-parser
        parser_create_repo = self.subparsers.add_parser('create-repo',\
                help='Create pulp repository', \
                usage='%(prog)s  REPONAME --arch ARCH --feed FEED')

        parser_create_repo.add_argument('name', metavar='name', \
                                            help='The name of your repo')

        parser_create_repo.add_argument('--arch', metavar='arch', \
                                        default='noarch', \
                                        help='The architecture of your repo')

        parser_create_repo.add_argument('--feed', metavar='feed', \
                                            default=None, \
                                            help='A feed repo for your repo')

        parser_create_repo.add_argument('--in', metavar='envs', \
                    nargs="+", \
                    dest='envs', \
                    default=self._default_envs, \
                    help='The environments in which to create your repository')

        parser_create_repo.set_defaults(ja=juicer.admin.create_repo)

        ##################################################################
        # Create the 'create_user' sub-parser
        parser_create_user = self.subparsers.add_parser('create-user',\
                help='Create pulp user', \
                usage='%(prog)s LOGIN --name FULLNAME --password PASSWORD')

        parser_create_user.add_argument('login', metavar='login', \
                                            help='Login user id for user')

        parser_create_user.add_argument('--name', metavar='name', \
                                            dest='name', \
                                            required=True, \
                                            help='Full name of user')

        parser_create_user.add_argument('--password', metavar='password', \
                                        dest='password', \
                                        nargs='*', \
                                        required=True, \
                                        action=PromptAction, \
                                        help='Plain text password for user')

        parser_create_user.add_argument('--in', metavar='envs', \
                        nargs="+", \
                        dest='envs', \
                        default=self._default_envs, \
                        help='The environments in which to create pulp user')

        parser_create_user.set_defaults(ja=juicer.admin.create_user)

        ##################################################################
        # Create the 'update-user' sub-parser
        parser_update_user = self.subparsers.add_parser('update-user',\
                help='Change user information', \
                usage='%(prog)s LOGIN --name FULLNAME --password PASSWORD')

        parser_update_user.add_argument('login', metavar='login', \
                                    help='Login user id for user to update')

        parser_update_user.add_argument('--name', metavar='name', \
                                            dest='name', \
                                            required=True, \
                                            help='Updated name of user')

        parser_update_user.add_argument('--password', metavar='password', \
                                        dest='password', \
                                        nargs='*', \
                                        required=True, \
                                        action=PromptAction, \
                                        help='Updated password for user')

        parser_update_user.add_argument('--in', metavar='envs', \
                        nargs="+", \
                        dest='envs', \
                        default=self._default_envs, \
                        help='The environments in which to create pulp user')

        parser_update_user.set_defaults(ja=juicer.admin.update_user)

        ##################################################################
        # Create the 'list_repos' sub-parser
        parser_list_repos = self.subparsers.add_parser('list-repos', \
                help='List all repos')

        parser_list_repos.add_argument('--in', metavar='envs', \
                               nargs="+", \
                               dest='envs', \
                               default=self._default_envs, \
                               help='The environments in which to list repos')

        parser_list_repos.set_defaults(ja=juicer.admin.list_repos)

        ##################################################################
        # Create the 'list_users' sub-parser
        parser_list_users = self.subparsers.add_parser('list-users', \
                help='List all users')

        parser_list_users.add_argument('--in', metavar='envs', \
                               nargs="+", \
                               dest='envs', \
                               default=self._default_envs, \
                               help='The environments in which to list users')

        parser_list_users.set_defaults(ja=juicer.admin.list_users)

        ##################################################################
        # Create the 'sync_repo' sub-parser

        parser_sync_repo = self.subparsers.add_parser('sync-repo', \
                help='Sync pulp repository')

        parser_sync_repo.add_argument('name', metavar='name', \
                                          help='The name of your repo')

        parser_sync_repo.add_argument('--in', metavar='envs', \
                      nargs="+", \
                      dest='envs', \
                      default=self._default_envs, \
                      help='The environments in which to sync your repository')

        parser_sync_repo.set_defaults(ja=juicer.admin.sync_repo)

        ##################################################################
        # Create the 'show_repo' sub-parser

        parser_show_repo = self.subparsers.add_parser('show-repo', \
                help='Show pulp repository')

        parser_show_repo.add_argument('name', metavar='name', \
                                          help='The name of your repo')

        parser_show_repo.add_argument('--in', metavar='envs', \
                      nargs="+", \
                      dest='envs', \
                      default=self._default_envs, \
                      help='The environments in which to show your repository')

        parser_show_repo.set_defaults(ja=juicer.admin.show_repo)

        ##################################################################
        # Create the 'show_user' sub-parser
        parser_show_user = self.subparsers.add_parser('show-user', \
                usage='%(prog)s LOGIN --in [ENV ...]', \
                help='Show pulp user')

        parser_show_user.add_argument('login', metavar='login', \
                                          help='Login user id for user')

        parser_show_user.add_argument('--in', metavar='envs', \
                              nargs="+", \
                              dest='envs', \
                              default=self._default_envs, \
                              help='The environments in which to show user')

        parser_show_user.set_defaults(ja=juicer.admin.show_user)

        ##################################################################
        # Create the 'delete_repo' sub-parser
        parser_delete_repo = self.subparsers.add_parser('delete-repo', \
                help='Delete pulp repository')

        parser_delete_repo.add_argument('name', metavar='name', \
                                            help='The name of your repo')

        parser_delete_repo.add_argument('--in', metavar='envs', \
                    nargs="+", \
                    dest='envs', \
                    default=self._default_envs, \
                    help='The environments in which to delete your repository')

        parser_delete_repo.set_defaults(ja=juicer.admin.delete_repo)

        ##################################################################
        # Create the 'delete_user' sub-parser
        parser_delete_user = self.subparsers.add_parser('delete-user', \
                help='Delete pulp user')

        parser_delete_user.add_argument('login', metavar='login', \
                                            help='Login user id for user')

        parser_delete_user.add_argument('--in', metavar='envs', \
                            nargs="+", \
                            dest='envs', \
                            default=self._default_envs, \
                            help='The environments in which to delete user')

        parser_delete_user.set_defaults(ja=juicer.admin.delete_user)

        ##################################################################
        # Create the 'role_add' sub-parser
        parser_role_add = self.subparsers.add_parser('role-add', \
                help='Add user to role')

        parser_role_add.add_argument('--login', metavar='login', \
                                         help='Login user id for user', \
                                         required=True)

        parser_role_add.add_argument('--role', metavar='role', \
                                         help='Role to add user to', \
                                         required=True)

        parser_role_add.add_argument('--in', metavar='envs', \
                         nargs="+", \
                         dest='envs', \
                         default=self._default_envs, \
                         help='The environments in which to add user to role')

        parser_role_add.set_defaults(ja=juicer.admin.role_add)

        ##################################################################
        # Create the 'list_roles' sub-parser
        parser_list_roles = self.subparsers.add_parser('list-roles', \
                help='List all roles')

        parser_list_roles.add_argument('--in', metavar='envs', \
                               nargs="+", \
                               dest='envs', \
                               default=self._default_envs, \
                               help='The environments in which to list roles')

        parser_list_roles.set_defaults(ja=juicer.admin.list_roles)
