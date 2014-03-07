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

        self.parser.add_argument('-v', action='count',
                                 default=1,
                                 help='Increase the verbosity (up to 3x)')

        self.parser.add_argument('-V', '--version', action='version',
                                 version="juicer-admin-%s"
                                 % juicer.utils.juicer_version())

        ##################################################################
        # Keep the different commands separate
        self.subparsers = self.parser.add_subparsers(title='Commands',
                                                     dest='command',
                                                     description='\'%(prog)s COMMAND -h\' for individual help topics')

        ##################################################################
        # Create the 'repo' sub-parser
        parser_repo = self.subparsers.add_parser('repo',
                                                 help='Repo operations')

        subparser_repo = parser_repo.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'user' sub-parser
        parser_user = self.subparsers.add_parser('user',
                                                 help='User operations')

        subparser_user = parser_user.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'role' sub-parser
        parser_role = self.subparsers.add_parser('role',
                                                 help='Role operations')

        subparser_role = parser_role.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'repo create' sub-parser
        parser_repo_create = subparser_repo.add_parser('create',
                                                       help='Create pulp repository',
                                                       usage='%(prog)s REPONAME [--feed FEED] [--checksum-type CHECKSUM-TYPE] [--in ENV [...]]')

        parser_repo_create.add_argument('name', metavar='name',
                                        help='The name of your repo')

        parser_repo_create.add_argument('--feed', metavar='feed',
                                        default=None,
                                        help='A feed repo for your repo')

        parser_repo_create.add_argument('--checksum-type', metavar='checksum_type',
                                        default='sha256',
                                        choices=['sha26', 'sha'],
                                        help='Checksum-type used for meta-data generation (one of: sha26, sha)')

        parser_repo_create.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to create your repository')

        parser_repo_create.set_defaults(ja=juicer.admin.create_repo)

        ##################################################################
        # Create the 'repo import' sub-parser
        import_description = """This will create repositories matching the definitions in the repo
def file. Repositories which already exist will be updated. See the
"repo import" and "Repo Def Format" sections in juicer-admin(1) for
instructions on how to write a proper repo def file."""

        import_epilog = """See "Exit Codes" in juicer-admin(1) for a description of how the
'--noop' flag alters the exit code."""

        parser_repo_import = subparser_repo.add_parser('import',
                                                       help='Create pulp repositories from an imported definition',
                                                       usage='%(prog)s FROM_FILE [--noop]',
                                                       description=import_description,
                                                       epilog=import_epilog)

        parser_repo_import.add_argument('from_file', default=None,
                                        help='Repository definition file in JSON format')

        parser_repo_import.add_argument('--noop', '--dry-run', '-n',
                                        default=False, action='store_true',
                                        help="Don't create the repos, just show what would have happened")

        parser_repo_import.set_defaults(ja=juicer.admin.import_repo)

        ##################################################################
        # Create the 'repo export' sub-parser

        export_description = """This dumps a standard juicer format repository definition for all
of you repos. Note that this may take a long time to finish."""

        parser_repo_export = subparser_repo.add_parser('export',
                                                       help='Export pulp repositories into a juicer repo def file.',
                                                       usage='%(prog)s',
                                                       description=export_description)

        parser_repo_export.add_argument('--out', '-o',
                                        default="repodefs-%s.json" % juicer.utils.iso_date_str(),
                                        help="File to write the output to. Use a single hypen, -, for stdout. Default is repodefs-ISO8601_FORMAT.json (YYYY-MM-DDTHH:MM:SS[.mmmmmm][+HH:MM])")

        parser_repo_export.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to export repo definitions.')

        parser_repo_export.add_argument('--pretty', '-p',
                                        default=False, action='store_true',
                                        help="Pretty-print the export.")

        parser_repo_export.set_defaults(ja=juicer.admin.export_repo)

        ##################################################################
        # Create the 'user create' sub-parser
        parser_user_create = subparser_user.add_parser('create',
                                                       help='Create pulp user',
                                                       usage='%(prog)s LOGIN --name FULLNAME --password PASSWORD \
                       \n\nYou will be prompted if the PASSWORD argument not supplied.')

        parser_user_create.add_argument('login', metavar='login',
                                        help='Login user id for user')

        parser_user_create.add_argument('--name', metavar='name',
                                        dest='name',
                                        required=True,
                                        help='Full name of user')

        parser_user_create.add_argument('--password', metavar='password',
                                        dest='password',
                                        nargs='*',
                                        required=True,
                                        action=PromptAction,
                                        help='Plain text password for user')

        parser_user_create.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to create pulp user')

        parser_user_create.set_defaults(ja=juicer.admin.create_user)

        ##################################################################
        # Create the 'user update' sub-parser
        parser_user_update = subparser_user.add_parser('update',
                                                       help='Change user information',
                                                       usage='%(prog)s LOGIN --name FULLNAME --password PASSWORD \
                       \n\nYou will be prompted if the PASSWORD argument not supplied.')

        parser_user_update.add_argument('login', metavar='login',
                                        help='Login user id for user to update')

        parser_user_update.add_argument('--name', metavar='name',
                                        dest='name',
                                        required=False,
                                        help='Updated name of user')

        parser_user_update.add_argument('--password', metavar='password',
                                        dest='password',
                                        nargs='*',
                                        required=False,
                                        action=PromptAction,
                                        help='Updated password for user')

        parser_user_update.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to create pulp user')

        parser_user_update.set_defaults(ja=juicer.admin.update_user)

        ##################################################################
        # Create the 'repo list' sub-parser
        parser_repo_list = subparser_repo.add_parser('list',
                                                     help='List all repos')

        parser_repo_list.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to list repos')

        parser_repo_list.add_argument('--json',
                                      action='store_true', default=False,
                                      help='Dump everything in JSON format')

        parser_repo_list.set_defaults(ja=juicer.admin.list_repos)

        ##################################################################
        # Create the 'user list' sub-parser
        parser_user_list = subparser_user.add_parser('list',
                                                     help='List all users')

        parser_user_list.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to list users')

        parser_user_list.set_defaults(ja=juicer.admin.list_users)

        ##################################################################
        # Create the 'repo sync' sub-parser

        parser_repo_sync = subparser_repo.add_parser('sync',
                                                     help='Sync pulp repository')

        parser_repo_sync.add_argument('name', metavar='name',
                                      help='The name of your repo')

        parser_repo_sync.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to sync your repository')

        parser_repo_sync.set_defaults(ja=juicer.admin.sync_repo)

        ##################################################################
        # Create the 'repo show' sub-parser

        parser_repo_show = subparser_repo.add_parser('show',
                                                     usage='%(prog)s name [...] [--json] --in [ENV ...]',
                                                     help='Show pulp repository(s)')

        parser_repo_show.add_argument('name', metavar='name',
                                      nargs="+",
                                      help='The name of your repo(s)')

        parser_repo_show.add_argument('--json',
                                      action='store_true', default=False,
                                      help='Dump everything in JSON format')

        parser_repo_show.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to show your repository')

        parser_repo_show.set_defaults(ja=juicer.admin.show_repo)

        ##################################################################
        # Create the 'user show' sub-parser
        parser_user_show = subparser_user.add_parser('show',
                                                     usage='%(prog)s LOGIN --in [ENV ...]',
                                                     help='Show pulp user')

        parser_user_show.add_argument('login', metavar='login',
                                      help='Login user id for user')

        parser_user_show.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to show user')

        parser_user_show.set_defaults(ja=juicer.admin.show_user)

        ##################################################################
        # Create the 'repo delete' sub-parser
        parser_repo_delete = subparser_repo.add_parser('delete',
                                                       help='Delete pulp repository')

        parser_repo_delete.add_argument('name', metavar='name',
                                        help='The name of your repo')

        parser_repo_delete.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to delete your repository')

        parser_repo_delete.set_defaults(ja=juicer.admin.delete_repo)

        ##################################################################
        # Create the 'user delete' sub-parser
        parser_user_delete = subparser_user.add_parser('delete',
                                                       help='Delete pulp user')

        parser_user_delete.add_argument('login', metavar='login',
                                        help='Login user id for user')

        parser_user_delete.add_argument('--in', metavar='envs',
                                        nargs="+",
                                        dest='envs',
                                        default=self._default_envs,
                                        help='The environments in which to delete user')

        parser_user_delete.set_defaults(ja=juicer.admin.delete_user)

        ##################################################################
        # Create the 'role add' sub-parser
        parser_role_add = subparser_role.add_parser('add',
                                                    help='Add user to role')

        parser_role_add.add_argument('--login', metavar='login',
                                     help='Login user id for user',
                                     required=True)

        parser_role_add.add_argument('--role', metavar='role',
                                     help='Role to add user to',
                                     required=True)

        parser_role_add.add_argument('--in', metavar='envs',
                                     nargs="+",
                                     dest='envs',
                                     default=self._default_envs,
                                     help='The environments in which to add user to role')

        parser_role_add.set_defaults(ja=juicer.admin.role_add)

        ##################################################################
        # Create the 'role list' sub-parser
        parser_role_list = subparser_role.add_parser('list',
                                                     help='List all roles')

        parser_role_list.add_argument('--in', metavar='envs',
                                      nargs="+",
                                      dest='envs',
                                      default=self._default_envs,
                                      help='The environments in which to list roles')

        parser_role_list.set_defaults(ja=juicer.admin.list_roles)
