from __future__ import with_statement
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

import juicer.common.RPM
import juicer.utils.Log
import juicer.utils
import os
import os.path


CART_LOCATION = os.path.expanduser("~/.juicer-carts")


class Cart(object):
    def __init__(self, name, autoload=False, autosync=False):
        """
        After a cart is instantiated there are two ways to fill it.

        1. Manually: Use the add_repo() method.
        2. Automaticaly: From a json file with the load() method.

        Setting `autoload` to `True` will call the load() method
        automatically.
        """
        self.name = name
        self.repo_items_hash = {}
        self.remotes_storage = os.path.expanduser(os.path.join(CART_LOCATION, "%s-remotes" % name))

        if autoload:
            juicer.utils.Log.log_notice("[CART:%s] Auto-loading cart items" % self.name)
            self.load(name)

            if autosync:
                juicer.utils.Log.log_notice("[CART:%s] Auto-syncing remote cart items" % self.name)
                self.sync_remotes()
        elif (not autoload) and autosync:
            juicer.utils.Log.log_warn("[CART:%s] Auto-sync requested, but autoload not enabled. Skipping..." % self.name)

    def add_repo(self, name, items):
        """
        Build up repos

        `name` - Name of this repo.
        `items` - List of paths to rpm.
        """
        juicer.utils.Log.log_debug("[CART:%s] Adding %s items to repo '%s'" % \
                                       (self.name, len(items), name))
        # We can't just straight-away add all of `items` to the
        # repo. `items` may be composed of a mix of local files, local
        # directories, remote files, and remote directories. We need
        # to filter and validate each item.
        self.repo_items_hash[name] = juicer.utils.filter_package_list(items)

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

    def sign_items(self, key):
        """
        Sign the items in the cart with a GPG key.
        """
        pass

    def sync_remotes(self):
        """
        Pull down all non-local items and save them into remotes_storage.
        """
        synced_items = {}

        for repo, items in self.iterrepos():
            syncs = []
            for rpm in items:
                rpm_obj = juicer.common.RPM.RPM(rpm)
                rpm_obj.sync(self.remotes_storage)

                if rpm_obj.modified:
                    syncs.append((rpm, rpm_obj.path))

            if syncs:
                synced_items[repo] = syncs

        for repo in synced_items.keys():
            for source, path in synced_items[repo]:
                juicer.utils.Log.log_debug("Source RPM modified. New 'path': %s" % rpm)
                self._update(repo, source, path)

        for repo, items in self.iterrepos():
            juicer.utils.Log.log_info("Sanity checking items for repo '%s'" % repo)
            not_rpms = filter(lambda r: not juicer.utils.is_rpm(r), items)

            if not_rpms:
                juicer.utils.Log.log_warn("The following items are not actually RPMs:")
                for i in not_rpms:
                    juicer.utils.Log.log_warn(i)



    def _update(self, repo, current, new):
        self.repo_items_hash[repo].remove(current)
        self.repo_items_hash[repo].append(new)

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
