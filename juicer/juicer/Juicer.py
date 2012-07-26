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
import os
import time
import rpm
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

    # starts the 3-step upload process
    def _init_up(self, query='/services/upload/', name='', cksum='', size='', \
            env='re'):
        data = {'name': name,
                'checksum': cksum,
                'size': size}

        _r = self.connectors[env].post(query, data)
        uid = juicer.utils.load_json_str(_r.content)['id']

        juicer.utils.Log.log_debug("Initialized upload process. POST returned with data: %s" % str(_r.content))

        return uid

    # continues 3-step upload process. this is where actual data transfer
    # occurs!
    def _append_up(self, query='/services/upload/append/', uid='', fdata='', env='re'):
        uri = query + uid + '/'
        juicer.utils.Log.log_notice("Appending to: %s" % uri)
        _r = self.connectors[env].put(uri, fdata, log_data=False, auto_create_json_str=False)

        juicer.utils.Log.log_debug("Continuing upload with append. PUT returned with data: %s" % str(_r.content))

        return juicer.utils.load_json_str(_r.content)

    # finalizes the 3-step upload process. this is where metadata is set
    def _import_up(self, query='/services/upload/import/', uid='', name='', \
                    ftype='rpm', cksum='', desc='', htype='md5', nvrea='', size='', \
                    lic='', group='', vendor='', req='', env='re'):
        data = {'uploadid': uid,
                'metadata': {
                    'type': ftype,
                    'checksum': cksum,
                    'description': desc,
                    'hashtype': htype,
                    'pkgname': name,
                    'nvrea': nvrea,
                    'size': size,
                    'license': lic,
                    'group': group,
                    'vendor': vendor,
                    'requires': req}}

        _r = self.connectors[env].post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Import error importing '%s'... server said: \n %s", name,
                                       juicer.utils.load_json_str(_r.content))
            _r.raise_for_status()

        juicer.utils.Log.log_debug("Finalized upload with data: %s" % str(_r.content))
        juicer.utils.Log.log_debug(juicer.utils.load_json_str(_r.content))
        return juicer.utils.load_json_str(_r.content)['id']

    # provides a simple interface for the pulp upload API
    def _upload_rpm(self, package, env):
        ts = rpm.TransactionSet()
        ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)

        rpm_fd = open(package, 'rb')
        pkg = ts.hdrFromFdno(rpm_fd)
        name = pkg['name']
        version = pkg['version']
        release = pkg['release']
        epoch = 0
        arch = pkg['arch']
        nvrea = tuple((name, version, release, epoch, arch))
        cksum = hashlib.md5(package).hexdigest()
        size = os.path.getsize(package)
        package_basename = os.path.basename(package)

        juicer.utils.Log.log_notice("Expected amount to seek: %s (package size by os.path.getsize)" % size)

        # initiate upload
        upload_id = self._init_up(name=package_basename, cksum=cksum, size=size)

        #create a statusbar
        if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
            pbar = ProgressBar(size)

        # read in rpm
        upload_flag = False
        total_seeked = 0
        rpm_fd.seek(0)
        while total_seeked < size:
            rpm_data = rpm_fd.read(Constants.UPLOAD_AT_ONCE)
            total_seeked += len(rpm_data)
            juicer.utils.Log.log_notice("Seeked %s data... (total seeked: %s)" % (len(rpm_data), total_seeked))
            upload_flag = self._append_up(uid=upload_id, fdata=rpm_data)
            if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
                pbar.update(len(rpm_data))
        if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
            pbar.finish()
        rpm_fd.close()

        juicer.utils.Log.log_notice("Seeked total data: %s" % total_seeked)

        # finalize upload
        rpm_id = ''
        if upload_flag == True:
            rpm_id = self._import_up(uid=upload_id, name=package_basename, cksum=cksum, \
                nvrea=nvrea, size=size)

        juicer.utils.Log.log_debug("RPM upload complete. New 'packageid': %s" % rpm_id)
        return rpm_id

    # provides a simple interface to include an rpm in a pulp repo
    def _include_rpm_in_repo(self, pkgid, env, repoid):
        query = '/repositories/' + repoid + '/add_package/'
        data = {'repoid': repoid,
                'packageid': [pkgid]}

        _r = self.connectors[env].post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
            self.connectors[env].delete('/packages/' + pkgid + '/')
            _r.raise_for_status()

    def _include_file_in_repo(self, fileid, env, repoid):
        query = '/repositories/' + repoid + '/add_file/'
        data = {'fileids': [fileid]}

        _r = self.connectors[env].post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
            print juicer.utils.load_json_str(_r.content)
            #self.connectors[env].delete('/files/' + fileid + '/')
            _r.raise_for_status()

    # forces pulp to generate metadata for the given repo
    def _generate_metadata(self, env, repoid):
        query = '/repositories/' + repoid + '/generate_metadata/'

        _r = self.connectors[env].post(query)

        juicer.utils.Log.log_debug("Attempted metadata update for repo: %s -> %s" % \
                                       (repoid, str(_r.content)))

        if _r.status_code == Constants.PULP_POST_CONFLICT:
            juicer.utils.Log.log_debug("Metadata update in %s already in progress...: " % \
                                           (repoid, str(_r.content)))
            while _r.status_code == Constants.PULP_POST_CONFLICT:
                time.sleep(3)
                _r = self.connectors[env].post(query)
        if not _r.status_code == Constants.PULP_POST_ACCEPTED:
            _r.raise_for_status()

    def _upload_file(self, file, env):
        fd = open(file, 'rb')
        name = os.path.basename(file)
        cksum = hashlib.sha256(file).hexdigest()
        size = os.path.getsize(file)
        nvrea = tuple((name, 0, 0, 0, 'noarch'))

        juicer.utils.Log.log_notice("Expected amount to seek: %s (file size by os.path.getsize)", size)

        # initiate upload
        upload_id = self._init_up(name=name, cksum=cksum, size=size)

        # create a statusbar
        if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
            pbar = ProgressBar(size)

        # read in file
        upload_flag = False
        total_seeked = 0
        fd.seek(0)

        while total_seeked < size:
            file_data = fd.read(Constants.UPLOAD_AT_ONCE)
            total_seeked += len(file_data)
            juicer.utils.Log.log_notice("Seeked %s data... (total seeked: %s)" % (len(file_data), total_seeked))
            upload_flag = self._append_up(uid=upload_id, fdata=file_data)
            if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
                pbar.update(len(file_data))
        if juicer.utils.Log.LOG_LEVEL_CURRENT == 1:
            pbar.finish()
        fd.close()

        juicer.utils.Log.log_notice("Seeked total data: %s" % total_seeked)

        # finalize upload
        file_id = ''
        if upload_flag == True:
            file_id = self._import_up(uid=upload_id, name=name, cksum=cksum, \
                                          ftype='file', nvrea=nvrea, size=size, htype='sha256')
        juicer.utils.Log.log_debug("FILE upload complete. New 'fileid': %s" % file_id)
        return file_id


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

        for item in items:
            juicer.utils.Log.log_debug("Processing item: '%s'" % item)
            juicer.utils.Log.log_info("Initiating upload of '%s' into '%s'" % (item, repoid))

            if juicer.utils.is_rpm(item):
                rpm_id = self._upload_rpm(item, env)
                self._include_rpm_in_repo(rpm_id, env, repoid)
            else:
                file_id = self._upload_file(item, env)
                self._include_file_in_repo(file_id, env, repoid)

        self._generate_metadata(env, repoid)

        return True

    def push(self, cart, env=None):
        """
        `cart` - Release cart to push

        Pushes a release cart to the pre-release environment.
        """
        juicer.utils.Log.log_debug("Initializing push of cart '%s'" % cart.name)
        #cart = juicer.common.Cart.Cart(cart_name, autoload=True, autosync=True)

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

            for item in items:
                link = juicer.utils.remote_url(self.connectors[env], env, repo, os.path.basename(item))
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

    def search_cart(self, query='/services/search/cart'):
        pass

    def search_rpm(self, name='', query='/services/search/packages/'):
        data = {'regex': True,
                'name': name}

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

                juicer.utils.Log.log_info('%s %s %s' % (package['name'], package['version'], link))

    def hello(self):
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
        juicer.utils.save_url_as(juicer.utils.remote_url(self.connectors[env], env, 'carts', cartname + '.json'), cart_file)
        juicer.utils.Log.log_info("pulled cart %s and saved to %s", cartname, cart_file)
        return True
