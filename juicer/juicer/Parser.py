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
import juicer.juicer
import juicer.utils


class Parser(object):
    def __init__(self):

        self.parser = argparse.ArgumentParser(\
                description='Manage release carts')
        juicer.juicer.parser = self.parser

        self._default_start_in = juicer.utils.get_login_info()[1]['start_in']
        self._default_envs = juicer.utils.get_environments()

        self.parser.add_argument('-v', action='count', \
                                default=1, \
                                help='Increase the verbosity (up to 3x)')

        ##################################################################
        # Keep the different commands separate
        subparsers = self.parser.add_subparsers(title='Commands', \
           dest='command', \
           description='\'%(prog)s COMMAND -h\' for individual help topics')

        ##################################################################
        # Create the 'create' sub-parser
        parser_create = subparsers.add_parser('create', \
                help='Create a cart with the items specified.', \
                usage='%(prog)s CARTNAME [-f rpm-manifest] ... [-r REPONAME items ... [ -r REPONAME items ...]]')

        parser_create.add_argument('cartname', metavar='cart-name', \
                                       help='Cart name')

        cgroup = parser_create.add_mutually_exclusive_group(required=True)

        cgroup.add_argument('-r', metavar=('reponame', 'item'), \
                                       action='append', \
                                       nargs='+', \
                                       help='Destination repo name')

        cgroup.add_argument('-f', metavar='rpm-manifest', \
                                    action='append', \
                                    help='RPM manifest for cart')

        parser_create.set_defaults(j=juicer.juicer.create)

        ##################################################################
        # Create the 'edit' sub-parser
        # parser_edit = subparsers.add_parser('edit', \
        #         help='Interactively edit a release cart.')

        # parser_edit.add_argument('cart-name', metavar='cartname', \
        #                              help='The name of your release cart')

        # parser_edit.set_defaults(j=juicer.juicer.edit)

        ##################################################################
        # Create the 'show' sub-parser
        parser_show = subparsers.add_parser('show', \
                help='Print the contents of a cart.')

        parser_show.add_argument('cartname', metavar='name', \
                                 help='The name of your cart')

        parser_show.set_defaults(j=juicer.juicer.show)

        ##################################################################
        # Create the 'update' sub-parser
        parser_update = subparsers.add_parser('update', \
                help='Update a release cart with items.', \
                usage='%(prog)s CARTNAME [-f rpm-manifest] ... [-r REPONAME items ... [-r REPONAME items...]]')

        parser_update.add_argument('cartname', metavar='cartname', \
                                       help='The name of your release cart')

        parser_update.add_argument('-r', metavar=('reponame', 'item'), \
                                       action='append', \
                                       nargs='+', \
                                       help='Destination repo name')

        parser_update.add_argument('-f', metavar='rpm-manifest', \
                                    action='append', \
                                    help='RPM manifest for cart')

        parser_update.set_defaults(j=juicer.juicer.update)

        ##################################################################
        # Create the 'pull' sub-parser
        parser_pull = subparsers.add_parser('pull', \
                help='Pull a release cart from remote.')

        parser_pull.add_argument('cartname', metavar='cartname', \
                                       help='The name of your release cart')

        parser_pull.set_defaults(j=juicer.juicer.pull)

        ##################################################################
        # Create the 'create-like' sub-parser
        # parser_createlike = subparsers.add_parser('create-like', \
        #         help='Create a new cart based off an existing one.')

        # parser_createlike.add_argument('cart-name', metavar='cartname', \
        #                            help='The name of your new release cart')

        # parser_createlike.add_argument('old-cart-name', \
        #         metavar='oldcartname', help='Cart to copy')

        # parser_createlike.add_argument('items', metavar='items', \
        #                                    nargs="+", \
        #                                    help='Cart name')

        # parser_createlike.set_defaults(j=juicer.juicer.createlike)

        ##################################################################
        # Create the 'push' sub-parser
        parser_push = subparsers.add_parser('push', \
                help='Pushes/Updates a cart on the pulp server.',
                usage='%(prog)s CARTNAME [--in [environment [environment ...]]] [-h]')

        parser_push.add_argument('cartname', metavar='cartname', \
                                    help='The name of your new release cart')

        parser_push.add_argument('--in', nargs='*', \
                metavar='environment', \
                default=[self._default_start_in], \
                help='The environments to push into.', \
                dest='environment')

        parser_push.set_defaults(j=juicer.juicer.push)

        ##################################################################
        # Create the 'search' sub-parser
        parser_search = subparsers.add_parser('search', \
                help='Search for an RPM in pulp.', \
                usage='%(prog)s rpmname [-r repo [repo]] [-c] [--in environment [environment]] [-h]')

        parser_search.add_argument('rpmname', metavar='rpmname', \
                                  help='The name of the rpm(s) to search for.')

        parser_search.add_argument('-r', nargs='*', metavar='repos', \
                default=[], help='The repo(s) to limit search scope to.')

        parser_search.add_argument('-c', '--carts', dest='carts', \
                action='store_true', \
                help="Search for the package in carts as well")

        parser_search.add_argument('--in', nargs='*', \
                metavar='environment', \
                default=[self._default_start_in], \
                help='The environments to limit search scope to.', \
                dest='environment')

        parser_search.set_defaults(j=juicer.juicer.search)

        ##################################################################
        # create the 'upload' sub-parser
        parser_upload = subparsers.add_parser('upload', \
                help='Upload the items specified into repos.', \
                usage='%(prog)s -r REPONAME items ... [ -r REPONAME items ...] [--in ENV ...]')

        parser_upload.add_argument('-r', metavar=('reponame', 'item'), \
                                       action='append', \
                                       nargs='+', \
                                       help='Destination repo name, items...')

        parser_upload.add_argument('--in', nargs='*', \
                metavar='environment', \
                default=[self._default_start_in], \
                help='The environments to upload into.', \
                dest='environment')

        parser_upload.set_defaults(j=juicer.juicer.upload)

        ##################################################################
        # create the 'hello' sub-parser
        parser_hello = subparsers.add_parser('hello', \
                help='Test your connection to the pulp server', \
                usage='%(prog)s hello [--in env ...]')

        parser_hello.add_argument('--in', nargs='*', \
                metavar='environment', \
                help='The environments to test the connection to.', \
                default=self._default_envs, \
                dest='environment')

        parser_hello.set_defaults(j=juicer.juicer.hello)

        ##################################################################
        # create the 'promote' sub-parser
        parser_promote = subparsers.add_parser('promote', \
                help='Promote a cart to the next environment')

        parser_promote.add_argument('cartname', metavar='cart', \
                help='The name of the cart to promote')

        parser_promote.set_defaults(j=juicer.juicer.promote)

        ##################################################################
        # create the 'merge' sub-parser
        parser_merge = subparsers.add_parser('merge', \
                help='Merge the contents of two carts', \
                usage='%(prog)s merge [CART1 [CART2 [CART3 ...]]] --name NAME')

        parser_merge.add_argument('carts', nargs="+",
                metavar='carts', \
                help='Two or more carts to merge')

        parser_merge.add_argument('--name',
                metavar='name', \
                help='Name of resultant cart, defaults to the first cart provided')

        parser_merge.set_defaults(j=juicer.juicer.merge)
