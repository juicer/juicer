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

import juicer.utils
import os
import os.path


CART_LOCATION = os.path.expanduser("~/.juicer-carts")


class Cart(object):
    def __init__(self, name):
        self.name = name
        self.repo_items_hash = {}

    def add_repo(self, name, items):
        """
        Build up repos

        `name` - Name of this repo.
        `items` - List of paths to rpm.
        """
        self.repo_items_hash[name] = []

        for item in items:
            for match in juicer.utils.find_pattern(item):
                self.repo_items_hash[name].append(match)

        self.repo_items_hash[name] = juicer.utils.dedupe(self.repo_items_hash[name])

    def load(self, json_file):
        """
        Build a cart from a json file
        """
        if not os.path.exists(CART_LOCATION):
            raise IOError("No carts currently exist (%s does not exist)" % CART_LOCATION)

        cart_file = os.path.join(CART_LOCATION, json_file)
        cart_body = juicer.utils.read_json_document(cart_file)

        for cart, items in cart_body.iteritems():
            self.add_repo(cart, items)

    def save(self):
        if not os.path.exists(CART_LOCATION):
            os.mkdir(CART_LOCATION)

        cart_file = os.path.join(CART_LOCATION, self.name)
        juicer.utils.write_json_document(cart_file, self.repo_items_hash)

    def __str__(self):
        output = []

        for repo, items in self.repo_items_hash.iteritems():
            output.append(repo.upper())
            # Underline the repo name
            output.append("-" * len(repo))
            # Add all the RPMs
            output.extend(items)
            output.append('')

        return "\n".join(output)
