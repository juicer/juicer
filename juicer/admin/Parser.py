# -*- coding: utf-8 -*-

import argparse
import juicer.admin

class Parser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Manage pulp')
        juicer.admin.parser = self.parser

        self.parser.add_argument('-v', action='count', \
                                help='Increase the verbosity (up to 3x)')

        ##################################################################
        # Keep the different commands separate
        self.subparsers = self.parser.add_subparsers(title='Commands', \
                                               dest='command', \
                                               description='\'%(prog)s COMMAND -h\' for individual help topics')

        ##################################################################
        # Create the 'create_repo' sub-parser
        parser_create_repo = self.subparsers.add_parser('create-repo', help='Create pulp repository')

        parser_create_repo.add_argument('name', metavar='name', \
                                            help='The name of your repo')

        parser_create_repo.add_argument('--in', metavar='envs', \
                                            nargs="+", \
                                            dest='envs', \
                                            default=['re', 'qa', 'stage', 'prod'], \
                                            help='The environments in which to create your repository')

        parser_create_repo.set_defaults(ja=juicer.admin.create_repo)


        ##################################################################
        # Create the 'create_user' sub-parser
        parser_create_user = self.subparsers.add_parser('create-user', help='Create pulp user')

        parser_create_user.add_argument('--name', metavar='name', \
                                            dest='name', \
                                            help='Full name of user')

        parser_create_user.add_argument('--login', metavar='login', \
                                            dest='login', \
                                            help='Login user id for user')

        parser_create_user.add_argument('--password', metavar='password', \
                                            dest='password', \
                                            help='Plain text password for user')

        parser_create_user.add_argument('--in', metavar='envs', \
                                            nargs="+", \
                                            dest='envs', \
                                            default=['re', 'qa', 'stage', 'prod'], \
                                            help='The environments in which to create pulp user')

        parser_create_user.set_defaults(ja=juicer.admin.create_user)


        ##################################################################
        # Create the 'list_repos' sub-parser
        parser_list_repos = self.subparsers.add_parser('list-repos', help='List all repos')

        parser_list_repos.add_argument('--in', metavar='envs', \
                                           nargs="+", \
                                           dest='envs', \
                                           default=['re', 'qa', 'stage', 'prod'], \
                                           help='The environments in which to list repos')

        parser_list_repos.set_defaults(ja=juicer.admin.list_repos)


        ##################################################################
        # Create the 'show_repo' sub-parser

        parser_show_repo = self.subparsers.add_parser('show-repo', help='Show pulp repository')

        parser_show_repo.add_argument('name', metavar='name', \
                                          help='The name of your repo')

        parser_show_repo.add_argument('--in', metavar='envs', \
                                          nargs="+", \
                                          dest='envs', \
                                          default=['re', 'qa', 'stage', 'prod'], \
                                          help='The environments in which to show your repository')

        parser_show_repo.set_defaults(ja=juicer.admin.show_repo)


        ##################################################################
        # Create the 'show_user' sub-parser
        parser_show_user = self.subparsers.add_parser('show-user', help='Show pulp user')

        parser_show_user.add_argument('login', metavar='login', \
                                          help='Login user id for user')

        parser_show_user.add_argument('--in', metavar='envs', \
                                          nargs="+", \
                                          dest='envs', \
                                          default=['re', 'qa', 'stage', 'prod'], \
                                          help='The environments in which to show user')

        parser_show_user.set_defaults(ja=juicer.admin.show_user)


        ##################################################################
        # Create the 'delete_repo' sub-parser
        parser_delete_repo = self.subparsers.add_parser('delete-repo', help='Delete pulp repository')

        parser_delete_repo.add_argument('name', metavar='name', \
                                            help='The name of your repo')

        parser_delete_repo.add_argument('--in', metavar='envs', \
                                            nargs="+", \
                                            dest='envs', \
                                            default=['re', 'qa', 'stage', 'prod'], \
                                            help='The environments in which to delete your repository')

        parser_delete_repo.set_defaults(ja=juicer.admin.delete_repo)


        ##################################################################
        # Create the 'delete_user' sub-parser
        parser_delete_user = self.subparsers.add_parser('delete-user', help='Delete pulp user')

        parser_delete_user.add_argument('login', metavar='login', \
                                            help='Login user id for user')

        parser_delete_user.add_argument('--in', metavar='envs', \
                                            nargs="+", \
                                            dest='envs', \
                                            default=['re', 'qa', 'stage', 'prod'], \
                                            help='The environments in which to delete user')

        parser_delete_user.set_defaults(ja=juicer.admin.delete_user)

        ##################################################################
        # Create the 'role_add' sub-parser
        parser_role_add = self.subparsers.add_parser('role-add', help='Add user to role')

        parser_role_add.add_argument('--login', metavar='login', \
                                         help='Login user id for user')

        parser_role_add.add_argument('--role', metavar='role', \
                                        help='Role to add user to')

        parser_role_add.add_argument('--in', metavar='envs', \
                                         nargs="+", \
                                         dest='envs', \
                                         default=['re', 'qa', 'stage', 'prod'], \
                                         help='The environments in which to add user to role')

        parser_role_add.set_defaults(ja=juicer.admin.role_add)


        ##################################################################
        # Create the 'list_roles' sub-parser
        parser_list_roles = self.subparsers.add_parser('list-roles', help='List all roles')

        parser_list_roles.add_argument('--in', metavar='envs', \
                                           nargs="+", \
                                           dest='envs', \
                                           default=['re', 'qa', 'stage', 'prod'], \
                                           help='The environments in which to list roles')

        parser_list_roles.set_defaults(ja=juicer.admin.list_roles)
