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

        self.parser = argparse.ArgumentParser(
            description='Manage release carts')
        juicer.juicer.parser = self.parser

        self._default_start_in = juicer.utils.get_login_info()[1]['start_in']
        self._default_envs = juicer.utils.get_environments()

        self.parser.add_argument('-v', action='count',
                                 default=1,
                                 help='Increase the verbosity (up to 3x)')

        self.parser.add_argument('-V', '--version', action='version',
                                 version="juicer-%s"
                                 % juicer.utils.juicer_version())

        ##################################################################
        # Keep the different commands separate
        subparsers = self.parser.add_subparsers(title='Commands',
                                                dest='command',
                                                description='\'%(prog)s COMMAND -h\' for individual help topics')

        ##################################################################
        # Create the 'cart' sub-parser
        parser_cart = subparsers.add_parser('cart',
                                            help='Cart operations')

        subparser_cart = parser_cart.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'rpm' sub-parser
        parser_rpm = subparsers.add_parser('rpm',
                                           help='RPM operations')

        subparser_rpm = parser_rpm.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'repo' sub-parser
        parser_repo = subparsers.add_parser('repo',
                                            help='Repo operations')

        subparser_repo = parser_repo.add_subparsers(dest='sub_command')

        ##################################################################
        # Create the 'cart create' sub-parser
        parser_cart_create = subparser_cart.add_parser('create',
                                                       help='Create a cart with the items specified.',
                                                       usage='%(prog)s CARTNAME [-f rpm-manifest] ... [-r REPONAME items ... [ -r REPONAME items ...]]')

        parser_cart_create.add_argument('cartname', metavar='cart-name',
                                        help='Cart name')

        cgroup = parser_cart_create.add_mutually_exclusive_group(required=True)

        cgroup.add_argument('-r', metavar=('reponame', 'item'),
                            action='append',
                            nargs='+',
                            help='Destination repo name')

        cgroup.add_argument('-f', metavar='rpm-manifest',
                            action='append',
                            help='RPM manifest for cart')

        parser_cart_create.set_defaults(j=juicer.juicer.create)

        ##################################################################
        # Create the 'edit' sub-parser
        # parser_edit = subparsers.add_parser('edit',
        #         help='Interactively edit a release cart.')

        # parser_edit.add_argument('cart-name', metavar='cartname',
        #                              help='The name of your release cart')

        # parser_edit.set_defaults(j=juicer.juicer.edit)

        ##################################################################
        # Create the 'cart show' sub-parser
        parser_cart_show = subparser_cart.add_parser('show',
                                                     usage='%(prog)s CARTNAME [--in [environment [environment ...]]] [-h]',
                                                     help='Print the contents of a cart.')

        parser_cart_show.add_argument('cartname', metavar='name',
                                      help='The name of your cart')

        parser_cart_show.add_argument('--in', nargs='*',
                                      metavar='environment',
                                      default=juicer.utils.get_environments(),
                                      help='Only show carts pushed to the given environment.',
                                      dest='environment')

        parser_cart_show.set_defaults(j=juicer.juicer.show)

        ##################################################################
        # Create the 'cart list' sub-parser
        parser_cart_list = subparser_cart.add_parser('list',
                                                     help='List all of your carts.')

        parser_cart_list.add_argument('cart_glob', metavar='cart_glob',
                                      nargs='*', default=['*'],
                                      help='A pattern to match cart names against (default: *)')

        parser_cart_list.set_defaults(j=juicer.juicer.list)

        ##################################################################
        # Create the 'cart update' sub-parser
        parser_cart_update = subparser_cart.add_parser('update',
                                                       help='Update a release cart with items.',
                                                       usage='%(prog)s CARTNAME [-f rpm-manifest] ... [-r REPONAME items ... [-r REPONAME items...]]')

        parser_cart_update.add_argument('cartname', metavar='cartname',
                                        help='The name of your release cart')

        parser_cart_update.add_argument('-r', metavar=('reponame', 'item'),
                                        action='append',
                                        nargs='+',
                                        help='Destination repo name')

        parser_cart_update.add_argument('-f', metavar='rpm-manifest',
                                        action='append',
                                        help='RPM manifest for cart')

        parser_cart_update.set_defaults(j=juicer.juicer.update)

        ##################################################################
        # Create the 'cart pull' sub-parser
        parser_cart_pull = subparser_cart.add_parser('pull',
                                                     help='Pull a release cart from remote.')

        parser_cart_pull.add_argument('cartname', metavar='cartname',
                                      help='The name of your release cart')

        parser_cart_pull.set_defaults(j=juicer.juicer.pull)

        ##################################################################
        # Create the 'create-like' sub-parser
        # parser_createlike = subparsers.add_parser('create-like',
        #         help='Create a new cart based off an existing one.')

        # parser_createlike.add_argument('cart-name', metavar='cartname',
        #                            help='The name of your new release cart')

        # parser_createlike.add_argument('old-cart-name',
        #         metavar='oldcartname', help='Cart to copy')

        # parser_createlike.add_argument('items', metavar='items',
        #                                    nargs="+",
        #                                    help='Cart name')

        # parser_createlike.set_defaults(j=juicer.juicer.createlike)

        ##################################################################
        # Create the 'cart push' sub-parser
        parser_cart_push = subparser_cart.add_parser('push',
                                                     help='Pushes/Updates a cart on the pulp server.',
                                                     usage='%(prog)s CARTNAME [--in [environment [environment ...]]] [-h]')

        parser_cart_push.add_argument('cartname', metavar='cartname',
                                      help='The name of your new release cart')

        parser_cart_push.add_argument('--in', nargs='*',
                                      metavar='environment',
                                      default=[self._default_start_in],
                                      help='The environments to push into.',
                                      dest='environment')

        parser_cart_push.set_defaults(j=juicer.juicer.push)

        ##################################################################
        # Create the 'cart delete' sub-parser
        parser_cart_delete = subparser_cart.add_parser('delete', \
                help='Delete a cart locally and on the pulp server.',
                usage='%(prog)s CARTNAME [-h]')

        parser_cart_delete.add_argument('cartname', metavar='cartname', \
                                    help='The name of the release cart to delete')

        parser_cart_delete.set_defaults(j=juicer.juicer.delete)

        ##################################################################
        # Create the 'rpm search' sub-parser
        parser_rpm_search = subparser_rpm.add_parser('search',
                                                     help='Search for an RPM in pulp.',
                                                     usage='%(prog)s rpmname [-r repo [repo]] [-c] [--in environment [environment]] [-h]')

        parser_rpm_search.add_argument('rpmname', metavar='rpmname',
                                       help='The name of the rpm(s) to search for.')

        parser_rpm_search.add_argument('-r', nargs='*', metavar='repos',
                                       default=[], help='The repo(s) to limit search scope to.')

        parser_rpm_search.add_argument('-c', '--carts', dest='carts',
                                       action='store_true',
                                       help="Search for the package in carts as well")

        parser_rpm_search.add_argument('--in', nargs='*',
                                       metavar='environment',
                                       default=[self._default_start_in],
                                       help='The environments to limit search scope to.',
                                       dest='environment')

        parser_rpm_search.set_defaults(j=juicer.juicer.search)

        ##################################################################
        # create the 'rpm upload' sub-parser
        parser_rpm_upload = subparser_rpm.add_parser('upload',
                                                     help='Upload the items specified into repos.',
                                                     usage='%(prog)s -r REPONAME items ... [ -r REPONAME items ...] [--in ENV ...]')

        parser_rpm_upload.add_argument('-r', metavar=('reponame', 'item'),
                                       action='append',
                                       nargs='+',
                                       required=True,
                                       help='Destination repo name, items...')

        parser_rpm_upload.add_argument('--in', nargs='*',
                                       metavar='environment',
                                       default=[self._default_start_in],
                                       help='The environments to upload into.',
                                       dest='environment')

        parser_rpm_upload.set_defaults(j=juicer.juicer.upload)

        ##################################################################
        # create the 'hello' sub-parser
        parser_hello = subparsers.add_parser('hello',
                                             help='Test your connection to the pulp server',
                                             usage='%(prog)s [--in env ...]')

        parser_hello.add_argument('--in', nargs='*',
                                  metavar='environment',
                                  help='The environments to test the connection to.',
                                  default=self._default_envs,
                                  dest='environment')

        parser_hello.set_defaults(j=juicer.juicer.hello)

        ##################################################################
        # create the 'cart promote' sub-parser
        parser_cart_promote = subparser_cart.add_parser('promote',
                                                        help='Promote a cart to the next environment')

        parser_cart_promote.add_argument('cartname', metavar='cart',
                                         help='The name of the cart to promote')

        parser_cart_promote.set_defaults(j=juicer.juicer.promote)

        ##################################################################
        # create the 'cart merge' sub-parser
        parser_cart_merge = subparser_cart.add_parser('merge',
                                                      help='Merge the contents of two carts',
                                                      usage='%(prog)s merge CART1 CART2 [CARTN ...]]] --into NEWCART')

        parser_cart_merge.add_argument('carts', nargs="+",
                                       metavar='carts',
                                       help='Two or more carts to merge')

        parser_cart_merge.add_argument('--into', '-i',
                                       metavar='new_cart_name',
                                       help='Name of resultant cart, defaults to updating CART1')

        parser_cart_merge.set_defaults(j=juicer.juicer.merge)

        ##################################################################
        # create the 'rpm delete' sub-parser
        parser_rpm_delete = subparser_rpm.add_parser('delete',
                                                     help='Remove rpm(s) from repositories',
                                                     usage='%(prog)s -r REPO-NAME ITEM ITEM ... --in [ENV ...]')

        parser_rpm_delete.add_argument('-r', metavar=('reponame', 'item'),
                                       required=True,
                                       action='append',
                                       nargs='+',
                                       help='Target repo filename, filename...')

        parser_rpm_delete.add_argument('--in', nargs='*',
                                       metavar='environment',
                                       help='The environments to test the connection to.',
                                       default=self._default_envs,
                                       dest='environment')

        parser_rpm_delete.set_defaults(j=juicer.juicer.delete_rpm)

        ##################################################################
        # create the 'publish' sub-parser
        parser_repo_publish = subparser_repo.add_parser('publish',
                                                        help='Publish a repository, this will regenerate metadata.',
                                                        usage='%(prog)s publish REPO --in [ENV ...]')

        parser_repo_publish.add_argument('repo', metavar='reponame',
                                         help='Target repo to publish.')

        parser_repo_publish.add_argument('--in', nargs='*',
                                         metavar='environment',
                                         help='The environments to publish repository in.',
                                         default=self._default_envs,
                                         dest='environment')

        parser_repo_publish.set_defaults(j=juicer.juicer.publish)
