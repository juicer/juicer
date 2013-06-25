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

from juicer.common.Constants import CART_LOCATION
from juicer.common import Constants
from juicer.common.Errors import *
import juicer.common.CartItem
import juicer.common.RPM
import juicer.utils.Log
import juicer.utils
import os
import os.path
import re


class Cart(object):
    def __init__(self, cart_name, autoload=False, autosync=False):
        """
        After a cart is instantiated there are two ways to fill it.

        1. Manually: Use the add_repo() method.
        2. Automaticaly: From a json file with the load() method.

        Setting `autoload` to `True` will call the load() method
        automatically.
        """
        self.cart_name = cart_name
        self.current_env = juicer.utils.get_login_info()[1]['start_in']
        self.repo_items_hash = {}
        self.remotes_storage = os.path.expanduser(os.path.join(CART_LOCATION, "%s-remotes" % cart_name))

        if autoload:
            juicer.utils.Log.log_notice("[CART:%s] Auto-loading cart items" % self.cart_name)
            self.load(cart_name)

            if autosync:
                juicer.utils.Log.log_notice("[CART:%s] Auto-syncing remote cart items" % self.cart_name)
                self.sync_remotes()
        elif (not autoload) and autosync:
            juicer.utils.Log.log_warn("[CART:%s] Auto-sync requested, but autoload not enabled. Skipping..." % self.cart_name)

    def __getitem__(self, repo):
        """ Return the items in the given repo """
        if repo in self.repo_items_hash:
            return self.repo_items_hash[repo]
        else:
            # TODO: Should this raise?
            return None

    def __setitem__(self, repo, items):
        """
        Just provides a shorthand way to call add_repo:

        cart_object['repo'] = items
        """
        self.add_repo(repo, items)

    def add_repo(self, repo_name, items):
        """
        Build up repos

        `name` - Name of this repo.
        `items` - List of paths to rpm.
        """
        juicer.utils.Log.log_debug("[CART:%s] Adding %s items to repo '%s'" % \
                                       (self.cart_name, len(items), repo_name))
        # We can't just straight-away add all of `items` to the
        # repo. `items` may be composed of a mix of local files, local
        # directories, remote files, and remote directories. We need
        # to filter and validate each item.
        items = juicer.utils.filter_package_list(items)
        cart_items = []
        for item in items:
            juicer.utils.Log.log_debug("Creating CartObject for %s" % item)
            i = juicer.common.CartItem.CartItem(item)
            cart_items.append(i)
        self.repo_items_hash[repo_name] = cart_items

    def load(self, json_file):
        """
        Build a cart from a json file
        """
        if not os.path.exists(CART_LOCATION):
            raise JuicerCartError("No carts currently exist (%s does not exist)" % CART_LOCATION)

        cart_file = os.path.join(CART_LOCATION, json_file)
        try:
            cart_body = juicer.utils.read_json_document(cart_file)
        except IOError as e:
            juicer.utils.Log.log_error('an error occured while accessing %s:' %
                    cart_file)
            raise JuicerError(e.message)

        self.cart_name = cart_body['_id']

        if cart_body['current_env'] == '':
                self.current_env = juicer.utils.get_login_info()[1]['start_in']
        else:
            self.current_env = cart_body['current_env']

        for repo, items in cart_body['repos_items'].iteritems():
            self.add_repo(repo, items)

    def save(self):
        if self.is_empty():
            juicer.utils.Log.log_error('Cart is empty, not saving anything')
            return None

        if not os.path.exists(CART_LOCATION):
            os.mkdir(CART_LOCATION)

        juicer.utils.write_json_document(self.cart_file(), self._cart_dict())

    def iterrepos(self):
        """
        A generator function that yields a (repo, [items]) tuple for
        each non-empty repo.
        """
        for repo, items in self.repo_items_hash.iteritems():
            if items:
                yield (repo, items)

    def sign_items(self, sign_with):
        """
        Sign the items in the cart with a GPG key.

        After everything is collected and signed all the cart items
        are issued a refresh() to sync their is_signed attributes.

        `sign_with` is a reference to the method that implements
        juicer.common.RpmSignPlugin.
        """
        cart_items = self.items()
        item_paths = [item.path for item in cart_items]
        sign_with(item_paths)

        for item in cart_items:
            item.refresh()

    def sync_remotes(self):
        """
        Pull down all non-local items and save them into remotes_storage.
        """
        juicer.utils.Log.log_info("The Cart.sync_remotes() method is deprecated! Stop using it!")

        for repo, items in self.iterrepos():
            for rpm in items:
                rpm.sync_to(self.remotes_storage)

        for repo, items in self.iterrepos():
            juicer.utils.Log.log_info("Sanity checking items for repo '%s'" % repo)
            not_rpms = filter(lambda r: not r.is_rpm, items)

            if not_rpms:
                juicer.utils.Log.log_warn("The following items are not actually RPMs:")
                map(juicer.utils.Log.log_warn, not_rpms)

    def is_empty(self):
        """
        return True if the cart has no items, False otherwise
        """
        for repo, items in self.iterrepos():
            if items:
                return False
        return True

    def repos(self):
        """
        Return all list of the repos it cart will upload items into.
        """
        return self.repo_items_hash.keys()

    def items(self):
        """ Build and return a list of all items in this cart """
        cart_items = []
        for repo, items in self.iterrepos():
            cart_items.extend(items)
        return cart_items

    def __str__(self):
        output = []

        for repo, items in self.repo_items_hash.iteritems():
            output.append(repo.upper())
            # Underline the repo name
            output.append("-" * len(repo))
            # Add all the RPMs
            output.extend([str(i) for i in items])
            output.append('')

        return "\n".join(output)

    def _cart_dict(self):
        output = {'_id': self.cart_name,
                'current_env': None,
                'repos_items': []}
        output['current_env'] = self.current_env

        repos_items = {}
        for repo in self.repos():
            repos_items[repo] = [str(i) for i in self[repo]]

        output['repos_items'] = repos_items
        return output

    def add_from_manifest(self, manifest, connectors, query='/content/units/rpm/search/'):
        pkg_list = juicer.utils.parse_manifest(manifest)
        env_re = re.compile('.*-%s' % self.current_env)

        urls = {}

        # packages need to be included in every repo they're in
        for pkg in pkg_list:
            juicer.utils.Log.log_debug("Finding %s %s %s ..." % \
                    (pkg['name'], pkg['version'], pkg['release']))

            data = {
                    'criteria': {
                        'filters': {
                            'name': pkg['name'],
                            'version': pkg['version'],
                            'release': pkg['release']
                            },
                        'sort': [['name', 'ascending']],
                        'fields': ['name', 'description', 'version', 'release', 'arch', 'filename']
                        },
                    'include_repos': 'true'
                    }

            _r = connectors[self.current_env].post(query, data)

            if not _r.status_code == Constants.PULP_POST_OK:
                raise JuicerPulpError('%s was not found in pulp. Additionally, a %s status code was returned' % (pkg['name'], _r.status_code))

            content = juicer.utils.load_json_str(_r.content)

            if len(content) == 0:
                juicer.utils.Log.log_debug("Searching for %s returned 0 results." % pkg['name'])
                continue

            for ppkg in content:
                for repo in ppkg['repository_memberships']:
                    if re.match(env_re, repo):
                        if repo not in urls:
                            urls[repo] = []

                        pkg_url = juicer.utils.remote_url(connectors[self.current_env], self.current_env, repo, ppkg['filename'])
                        urls[repo].append(pkg_url)

        for repo in urls:
            self[repo] = urls[repo]

    def cart_file(self):
        """
        return the path to the json cart file
        note: the file does not need to already exist to use this
        """
        return os.path.join(CART_LOCATION, self.cart_name) + '.json'
