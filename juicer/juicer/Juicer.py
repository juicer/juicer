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

from juicer.common import Constants
from juicer.utils.ProgressBar import ProgressBar
import juicer.common.Cart
import juicer.juicer
import juicer.utils
import juicer.utils.Upload
import os
import time
import re
import hashlib


class Juicer(object):
    def __init__(self, args):
        self.args = args

        (self.connectors, self._defaults) = juicer.utils.get_login_info()

        if 'environment' in self.args:
            for env in self.args.environment:
                try:
                    self.connectors[env].get()
                except Exception:
                    juicer.utils.Log.log_error("%s is not a server configured in juicer.conf" % env)
                    juicer.utils.Log.log_debug("Exiting...")
                    exit(1)

    # this is used to upload files to pulp
    def upload(self, env, repo, items=[]):
        """
        Nothing special happens here. This method recieves a
        destination repo, and a payload of `items` which will be
        uploaded into the target repo.

        Preparation: To use this method you must pre-process your
        upload list (`items`). Remotes must be fetched and saved
        locally. Directories must be recursed and replaced with their
        contents.

        Warning: this method trusts you to Do The Right Thing (TM),
        ahead of time and check file types before feeding them to it.

        `env` - name of the environment with the cart destination
        `repo` - should be a string, the detination repo name
        `items` - should be a list of paths to RPM files
        """
        repoid = "%s-%s" % (repo, env)

        juicer.utils.Log.log_debug("Beginning upload for %s" % repoid)

        # Determine if these files are all rpms and if we need to sign
        # them. If we signed them, check for sigs but don't
        # bail... Then continue normally.
        if self.connectors[env].requires_signature and all([juicer.utils.is_rpm(item) for item in items]):
            self.sign_rpms(items, env)
            if not juicer.utils.rpms_signed_p(items):
                juicer.utils.Log.log_debug("No RPMs have been signed!")
                #raise RunTimeException() Do we want to barf?
            else:
                juicer.utils.Log.log_debug("RPMs have a signature... we do not know if it is valid...")

        for item in items:
            juicer.utils.Log.log_debug("Processing item: '%s'" % item)
            juicer.utils.Log.log_info("Initiating upload of '%s' into '%s'" % (item, repoid))

            if juicer.utils.is_rpm(item):
                rpm_id = juicer.utils.upload_rpm(item, repoid, self.connectors[env])
            else:
                file_id = juicer.utils.upload_file(item, repoid, self.connectors[env])

        return True

    def push(self, cart, env=None):
        """
        `cart` - Release cart to push

        Pushes a release cart to the pre-release environment.
        """
        juicer.utils.Log.log_debug("Initializing push of cart '%s'" % cart.name)

        if not env:
            env = self._defaults['cart_dest']

        for repo, items in cart.iterrepos():
            if not juicer.utils.repo_exists_p(repo, self.connectors[env], env):
                juicer.utils.Log.log_info("repo '%s' doesn't exist in %s environment... skipping!",
                                          (repo, env))
                continue

            juicer.utils.Log.log_debug("Initiating upload for repo '%s'" % repo)
            self.upload(env, repo, items)

            if cart.name == 'upload-cart':
                continue

            links = [(item, juicer.utils.remote_url(self.connectors[env], env, repo, os.path.basename(item))) for item in items]
            for item, link in links:
                cart._update(repo, item, link)

        if cart.name != 'upload-cart':
            cart.save()
            self.publish(cart)

        return True

    def publish(self, cart, env=None):
        """
        `cart` - Release cart to publish

        Publish a release cart to the pre-release environment.
        """

        juicer.utils.Log.log_debug("Initializing publish of cart '%s'" % cart.name)

        if not env:
            env = self._defaults['cart_dest']

        cart_file = os.path.join(juicer.common.Cart.CART_LOCATION, cart.name)

        if not cart_file.endswith('.json'):
            cart_file += '.json'

        juicer.utils.Log.log_debug("Initializing upload of cart '%s' to cart repository" % cart.name)
        self.upload(env, 'carts', [cart_file])

        return True

    def create_manifest(self, cart_name, manifest, query='/services/search/packages/'):
        """
        `cart_name` - Name of this release cart
        `manifest` - str containing path to manifest file
        """
        cart_dest = self._defaults['cart_dest']
        env_re = re.compile('.*-%s' % cart_dest)

        cart = juicer.common.Cart.Cart(cart_name)
        try:
            pkg_list = juicer.utils.parse_manifest(manifest)
        except IOError as e:
            juicer.utils.Log.log_error(e.message)
            exit(1)

        urls = {}

        # packages need to be included in every repo they're in
        for pkg in pkg_list:
            juicer.utils.Log.log_debug("Finding %s %s %s ..." % \
                    (pkg['name'], pkg['version'], pkg['release']))

            data = {'name': pkg['name'],
                    'version': pkg['version'],
                    'release': pkg['release']}

            _r = self.connectors[cart_dest].post(query, data)

            if not _r.status_code == Constants.PULP_POST_OK:
                juicer.utils.Log.log_error('%s was not found in pulp. Additionally, a %s status code was returned' % (pkg['name']._r.status_code))
                exit(1)

            content = juicer.utils.load_json_str(_r.content)

            if len(content) == 0:
                juicer.utils.Log.log_debug("Searching for %s returned 0 results." % pkg['name'])
                continue

            ppkg = content[0]

            for repo in ppkg['repoids']:
                if re.match(env_re, repo):
                    if repo not in urls:
                        urls[repo] = []

                    pkg_url = juicer.utils.remote_url(self.connectors[cart_dest],
                        cart_dest, repo, ppkg['filename'])
                    urls[repo].append(pkg_url)

        for repo in urls:
            cart.add_repo(repo, urls[repo])

        cart.save()

        return cart

    def create(self, cart_name, cart_description):
        """
        `cart_name` - Name of this release cart
        `cart_description` - list of ['reponame', item1, ..., itemN] lists
        """
        cart = juicer.common.Cart.Cart(cart_name)

        # repo_items is a list that starts with the REPO name,
        # followed by the ITEMS going into the repo.
        for repo_items in cart_description:
            repo = repo_items[0]
            items = repo_items[1:]
            juicer.utils.Log.log_debug("Processing %s input items for repo '%s'." % (len(items), repo))

            cart.add_repo(repo, items)

        cart.save()

        return cart

    def show(self, cart_name):
        cart = juicer.common.Cart.Cart(cart_name)
        cart.load(cart_name)
        return str(cart)

    def search(self, name='', query='/services/search/packages/'):
        data = {'regex': True,
                'name': name}

        juicer.utils.Log.log_debug('Downloading all carts...')

        # download all cart (json) files and set up variables for use
        cart_dest = self._defaults['cart_dest']

        _r = self.connectors[cart_dest].get('/repositories/carts-%s/files/' % cart_dest)
        if not _r.status_code == Constants.PULP_GET_OK:
            raise IOError("Couldn't get cart list")

        cart_list = []

        for cart in juicer.utils.load_json_str(_r.content):
            cart_list.append(cart['filename'])

            juicer.utils.save_url_as(
                    juicer.utils.remote_url(self.connectors[cart_dest], cart_dest, 'carts', cart['filename']),
                    os.path.join(juicer.common.Cart.CART_LOCATION, cart['filename']))

        juicer.utils.Log.log_info('Packages:')

        for env in self.args.environment:
            juicer.utils.Log.log_debug("Querying %s server" % env)
            _r = self.connectors[env].post(query, data)

            if not _r.status_code == Constants.PULP_POST_OK:
                juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
                _r.raise_for_status()

            juicer.utils.Log.log_info('%s:' % str.upper(env))

            pkg_list = juicer.utils.load_json_str(_r.content)

            for package in pkg_list:
                # if the package is in a repo, show a link to the package in said repo
                # otherwise, show nothing
                if len(package['repoids']) > 0:
                    target = package['repoids'][0]

                    _r = self.connectors[env].get('/repositories/%s/' % target)
                    if not _r.status_code == Constants.PULP_GET_OK:
                        juicer.utils.Log.error_log("%s was not found as a repoid. A %s status code was returned" %
                                (target, _r.status_code))
                        exit(1)
                    repo = juicer.utils.load_json_str(_r.content)['name']

                    link = juicer.utils.remote_url(self.connectors[env], env, repo, package['filename'])
                else:
                    link = ''

                # if the package is in a cart, show the cart name
                carts = []

                for cart in cart_list:
                    juicer.utils.Log.log_debug('checking for %s in %s' % (package['name'], cart))

                    for line in open(os.path.join(juicer.common.Cart.CART_LOCATION, cart)):
                        if re.match('.*%s.*' % package['filename'], line):
                            carts.append(cart.rstrip('.json'))

                carts = ', '.join(carts)

                juicer.utils.Log.log_info('%s %s %s %s' % (package['name'], package['version'], link, carts))

    def hello(self):
        """
        Test pulp server connections defined in ~/.juicer.conf.
        """
        for env in self.args.environment:
            juicer.utils.Log.log_info("Trying to open a connection to %s, %s ...",
                                      env, self.connectors[env].base_url)
            try:
                _r = self.connectors[env].get()
                juicer.utils.Log.log_info("OK")
            except Exception:
                juicer.utils.Log.log_info("FAILED")
                continue

            juicer.utils.Log.log_info("Attempting to authenticate as %s",
                                      self.connectors[env].auth[0])

            _r = self.connectors[env].get('/repositories/')

            if _r.status_code == Constants.PULP_GET_OK:
                juicer.utils.Log.log_info("OK")
            else:
                juicer.utils.Log.log_info("FAILED")
                juicer.utils.Log.log_info("Server said: %s", _r.content)
                continue
        return True

    def pull(self, cartname=None, env=None):
        """
        `cartname` - Name of cart

        Pull remote cart from the pre release (base) environment
        """
        if not env:
            env = self._defaults['cart_dest']
        juicer.utils.Log.log_debug("Initializing pulling cart: %s ...", cartname)
        cart_file = os.path.join(juicer.common.Cart.CART_LOCATION, cartname)
        cart_file += '.json'
        juicer.utils.save_url_as(juicer.utils.remote_url(self.connectors[env], env, 'carts', cartname + '.json'),
                                 cart_file)
        juicer.utils.Log.log_info("pulled cart %s and saved to %s", cartname, cart_file)
        return True

    def promote(self, name):
        """
        `name` - name of cart

        Promote a cart from its current environment to the next in the chain.
        """
        cart = juicer.common.Cart.Cart(name=name, autoload=True, autosync=True)
        old_env = cart.current_env
        cart.current_env = juicer.utils.get_next_environment(cart.current_env)

        juicer.utils.Log.log_debug("Syncing down rpms...")
        cart.sync_remotes()

        juicer.utils.Log.log_info("Promoting %s from %s to %s" %
                (name, old_env, cart.current_env))

        for repo, items in cart.iterrepos():
            juicer.utils.Log.log_debug("Promoting %s to %s in %s" %
                    (items, repo, cart.current_env))
            self.upload(cart.current_env, repo, items)

        cart.save()

        self.publish(cart)

    def sign_rpms(self, rpm_files=None, env=None):
        """
        `rpm_files` - A list of paths to RPM files.

        Will attempt to load the rpm_sign_plugin defined in
        ~/.juicer.conf which must be a plugin inheriting from
        juicer.common.RpmSignPlugin. If available, we'll call
        rpm_sign_plugin.sign_rpms(rpm_files) and return.
        """
        juicer.utils.Log.log_notice("%s requires RPM signatures ... checking for rpm_sign_plugin definition ...", env)
        module_name = self._defaults['rpm_sign_plugin']
        if self._defaults['rpm_sign_plugin']:
            juicer.utils.Log.log_notice("found rpm_sign_plugin definition %s ... attempting to load ...",
                                       self._defaults['rpm_sign_plugin'])

            try:
                rpm_sign_plugin = __import__(module_name, fromlist=[module_name])
                juicer.utils.Log.log_notice("successfully loaded %s ...", module_name)
                plugin_object = getattr(rpm_sign_plugin, module_name.split('.')[-1])
                signer = plugin_object()
                signer.sign_rpms(rpm_files)
            except ImportError as e:
                juicer.utils.Log.log_notice("there was a problem using %s ... error: %s",
                                            module_name, e)
        else:
            juicer.utils.Log.log_info("did not find an rpm_sign_plugin!")
        return True
