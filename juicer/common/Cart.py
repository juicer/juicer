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

import juicer.utils.Log
import juicer.utils
import os
import os.path


CART_LOCATION = os.path.expanduser("~/.juicer-carts")


class Cart(object):
    def __init__(self, name, autoload=False):
        """
        After a cart is instantiated there are two ways to fill it.

        1. Manually: Use the add_repo() method.
        2. Automaticaly: From a json file with the load() method.

        Setting `autoload` to `True` will call the load() method
        automatically.
        """
        self.name = name
        self.repo_items_hash = {}

        if autoload:
            self.load(name)

    def add_repo(self, name, items):
        """
        Build up repos

        `name` - Name of this repo.
        `items` - List of paths to rpm.
        """
        juicer.utils.Log.log_debug("[CART:%s] Adding %s items to repo '%s'" % \
                                       (self.name, len(items), name))
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

    def iterrepos(self):
        """
        A generator function that yields a (repo, [items]) tuple for
        each non-empty repo.
        """
        for repo, items in self.repo_items_hash.iteritems():
            if items:
                yield (repo, items)

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


# TODO: Refactor this fetching kind of logic
# into... cart processing? Perhaps a prep type
# action to sync remotes to local.
# # https://path.to/package.rpm
# elif re.match('https?://.*', item):
#     # download item and upload
#     if not re.match('.*\.rpm', item):
#         raise TypeError('{0} is not an rpm'.format(item))
#     filename = re.match('https?://.*/(.*\.rpm)', item).group(1)
#     remote = requests.get(item, env)
#     with open(filename, 'wb') as data:
#         data.write(remote.content())
#     rpm_id = self._upload_rpm(filename, env)
#     self._include_rpm_in_repo(rpm_id, env, repoid)
#     os.remove(filename)
