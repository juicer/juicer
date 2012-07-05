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

import argparse
import juicer.juicer


class Parser(object):
    def __init__(self):

        self.parser = argparse.ArgumentParser(\
                description='Manage release carts')
        juicer.juicer.parser = self.parser

        self.parser.add_argument('-v', action='count', \
                                help='Increase the verbosity (up to 3x)')

       ##################################################################
       # Keep the different commands separate
        subparsers = self.parser.add_subparsers(title='Commands', \
           dest='command', \
           description='\'%(prog)s COMMAND -h\' for individual help topics')

       ##################################################################
       # Create the 'create' sub-parser
        parser_create = subparsers.add_parser('create', \
                help='Create a cart with the items specified.')

        parser_create.add_argument('cart-name', metavar='cartname', \
                                       help='Cart name')

        parser_create.add_argument('-r', metavar='reponame', \
                                       help='Repo name')

        parser_create.add_argument('items', metavar='items', \
                                       nargs="+", \
                                       help='ITEM')

        parser_create.set_defaults(j=juicer.juicer.create)

        ##################################################################
        # Create the 'edit' sub-parser
        parser_edit = subparsers.add_parser('edit', \
                help='Interactively edit a release cart.')

        parser_edit.add_argument('cart-name', metavar='cartname', \
                                     help='The name of your release cart')

        parser_edit.set_defaults(j=juicer.juicer.edit)

        ##################################################################
        # Create the 'show' sub-parser
        parser_show = subparsers.add_parser('show', \
                help='Print the contents of a cart.')

        parser_show.add_argument('cart-name', metavar='name', \
                                     help='The name of your cart')

        parser_show.set_defaults(j=juicer.juicer.show)

        ##################################################################
        # Create the 'update' sub-parser
        parser_update = subparsers.add_parser('update', \
                help='Update a release cart with items.')

        parser_update.add_argument('cart-name', metavar='cartname', \
                                       help='The name of your release cart')

        parser_show.add_argument('items', metavar='items', \
                                     nargs="+", \
                                     help='Cart name')

        parser_update.set_defaults(j=juicer.juicer.update)

        ##################################################################
        # Create the 'create-like' sub-parser
        parser_createlike = subparsers.add_parser('create-like', \
                help='Create a new cart based off an existing one.')

        parser_createlike.add_argument('cart-name', metavar='cartname', \
                                   help='The name of your new release cart')

        parser_createlike.add_argument('old-cart-name', \
                metavar='oldcartname', help='Cart to copy')

        parser_createlike.add_argument('items', metavar='items', \
                                           nargs="+", \
                                           help='Cart name')

        parser_createlike.set_defaults(j=juicer.juicer.createlike)

        ##################################################################
        # Create the 'publish' sub-parser
        parser_publish = subparsers.add_parser('publish', \
                help='Publishes/Updates a cart on the pulp server.')

        parser_publish.add_argument('cart-name', metavar='cartname', \
                                    help='The name of your new release cart')

        parser_publish.set_defaults(j=juicer.juicer.publish)

        ##################################################################
        # Create the 'cart_search' sub-parser
        parser_cartsearch = subparsers.add_parser('cart-search', \
                help='Search for a cart in pulp.')

        parser_cartsearch.add_argument('cartname', metavar='cartname', \
                                   help='The name of the cart to search for')

        parser_cartsearch.set_defaults(j=juicer.juicer.cartsearch)

        ##################################################################
        # Create the 'rpm_search' sub-parser
        parser_rpmsearch = subparsers.add_parser('rpm-search', \
                help='Search for an RPM in pulp.', \
                usage='%(prog)s rpmname [...] [-r repo [repo]] \
                [--in environment [environment]] [-h]')

        parser_rpmsearch.add_argument('rpmname', metavar='rpmname', \
                                          nargs='+', \
                                  help='The name of the rpm(s) to search for.')

        parser_rpmsearch.add_argument('-r', nargs='*', metavar='repos', \
                default=[], help='The repo(s) to limit search scope to.')

        parser_rpmsearch.add_argument('--in', nargs='*', \
                metavar='environment', \
                help='The environments to limit search scope to.', \
                dest='environment')

        parser_rpmsearch.set_defaults(j=juicer.juicer.rpmsearch)

        ##################################################################
        # create the 'upload' sub-parser
        parser_upload = subparsers.add_parser('upload', \
                help='Upload an item into pulp', \
                usage='%(prog)s item [item ...] [-r repo [repo ...]] \
                [--in environment [environment ...]]')

        parser_upload.add_argument('item', metavar='item', \
                nargs='+', \
                help='an item (rpm, directory or url) to be uploaded')

        parser_upload.add_argument('-r', nargs='*', metavar='repo', \
                dest='repos', \
                default=[], help='The repo(s) to upload into.')

        parser_upload.add_argument('--in', nargs='*', \
                metavar='environment', \
                help='The environments to upload into.', \
                dest='environment')

        parser_upload.set_defaults(j=juicer.juicer.upload)
