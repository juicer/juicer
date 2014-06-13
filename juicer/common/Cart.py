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

    def keys(self):
        """
        Get repo keys.
        """
        return self.repo_items_hash.keys()

    def load(self, json_file):
        """
        Build a cart from a json file
        """
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

        juicer.utils.write_json_document(self.cart_file(), self._cart_dict())
        juicer.utils.Log.log_info("Saved cart '%s'." % self.cart_name)

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

    def sync_remotes(self, force=False):
        """
        Pull down all non-local items and save them into remotes_storage.
        """
        connectors = juicer.utils.get_login_info()[0]
        for repo, items in self.iterrepos():
            repoid = "%s-%s" % (repo, self.current_env)
            for rpm in items:
                # don't bother syncing down if it's already in the pulp repo it needs to go to
                if not rpm.path.startswith(juicer.utils.pulp_repo_path(connectors[self.current_env], repoid)) or force:
                    rpm.sync_to(self.remotes_storage)
                else:
                    juicer.utils.Log.log_debug("Not syncing %s because it's already in pulp" % rpm.path)

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
        return juicer.utils.create_json_str(self._cart_dict(), indent=4)

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
                            'release': pkg['release'],
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
                    ending = "-%s" % self.current_env
                    simple_repo = repo[:-len(ending)]
                    if simple_repo not in urls:
                        urls[simple_repo] = []

                    pkg_url = juicer.utils.remote_url(connectors[self.current_env], self.current_env, repo, ppkg['filename'])
                    urls[simple_repo].append(pkg_url)

        for repo in urls:
            self[repo] = urls[repo]

    def cart_file(self):
        """
        return the path to the json cart file
        note: the file does not need to already exist to use this
        """
        return os.path.join(CART_LOCATION, self.cart_name) + '.json'

    def implode(self, env):
        """
        remove all trace of this cart: delete the file(s) on the local
        filesystem and delete the entry from the database
        """
        juicer.utils.Log.log_debug("imploding %s" % self.cart_name)

        # rm -r self.remotes_storage()
        if os.path.exists(self.remotes_storage):
            for item in os.listdir(self.remotes_storage):
                ipath = os.path.expanduser(self.remotes_storage + '/' + item)
                if os.path.exists(ipath):
                    juicer.utils.Log.log_debug("removing %s" % ipath)
                    os.remove(ipath)
                juicer.utils.Log.log_debug("removing %s's remote item storage dir" % self.cart_name)
                os.rmdir(self.remotes_storage)

        # rm cart_file()
        if os.path.exists(self.cart_file()):
            juicer.utils.Log.log_debug("removing %s's cart file" % self.cart_name)
            os.remove(self.cart_file())

        # db.carts.delete(self.name)
        juicer.utils.Log.log_debug("removing %s from the database" % self.cart_name)
        juicer.utils.cart_db()[env].remove({'_id': self.cart_name})
