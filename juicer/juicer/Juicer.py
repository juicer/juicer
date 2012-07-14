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
import juicer.common.Cart
import juicer.juicer
import juicer.utils
import re
import os
import time
import rpm
import hashlib
import requests


class Juicer(object):
    def __init__(self, args):
        self.args = args

        (self.connectors, self._defaults) = juicer.utils.get_login_info()

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
    def _append_up(self, query='/services/upload/append/', uid='', fdata='', \
                    env='re'):
        uri = query + uid + '/'
        data = {'file-id': uid,
                'file-data': fdata.decode('utf-8', 'replace')}

        _r = self.connectors[env].put(uri, data)

        juicer.utils.Log.log_debug("Continuing upload with append. PUT returned with data: %s" % str(_r.content))

        return juicer.utils.load_json_str(_r.content)

    # finalizes the 3-step upload process. this is where metadata is set
    def _import_up(self, query='/services/upload/import/', uid='', name='', \
                    ftype='rpm', cksum='', htype='md5', nvrea='', size='', \
                    lic='', group='', vendor='', req='', env='re'):
        data = {'uploadid': uid,
                'metadata': {
                    'type': ftype,
                    'checksum': cksum,
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
            _r.raise_for_status()

        juicer.utils.Log.log_debug("Finalized upload with data: %s" % str(_r.content))
        from pprint import pprint as pp
        pp(_r.content)
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

        # initiate upload
        upload_id = self._init_up(name=package_basename, cksum=cksum, size=size)

        # read in rpm
        upload_flag = False
        while True:
            rpm_data = rpm_fd.read(Constants.UPLOAD_AT_ONCE)

            if not rpm_data:
                break

            upload_flag = self._append_up(uid=upload_id, fdata=rpm_data)

        rpm_fd.close()

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

    # forces pulp to generate metadata for the given repo
    def _generate_metadata(self, env, repoid):
        query = '/repositories/' + repoid + '/generate_metadata/'

        _r = self.connectors[env].post(query)

        if _r.status_code == Constants.PULP_POST_CONFLICT:
            while _r.status_code == Constants.PULP_POST_CONFLICT:
                time.sleep(3)
                _r = self.connectors[env].post(query)
        if not _r.status_code == Constants.PULP_POST_ACCEPTED:
            _r.raise_for_status()

    # this is used to upload files to pulp
    def upload(self, items=[], repos=[], envs=[]):

        for env in envs:
            juicer.utils.Log.log_debug("Beginning upload for environment: %s" % env)
            for repo in repos:
                juicer.utils.Log.log_debug("Processing items for repository: '%s'" % repo)
                for item in items:
                    repoid = "%s-%s" % (repo, env)
                    juicer.utils.Log.log_debug("Processing item: '%s'" % item)
                    juicer.utils.Log.log_info("Initiating upload of '%s' into '%s-%s'" % (item, repo, env))
                    # path/to/package.rpm
                    if os.path.isfile(item):
                        # process individual file
                        if not re.match('.*\.rpm', item):
                            raise TypeError("{0} is not an rpm".format(item))

                        rpm_id = self._upload_rpm(item, env)
                        self._include_rpm_in_repo(rpm_id, env, repoid)

                    # path/to/packages/
                    elif os.path.isdir(item):
                        # process files in dir
                        for package in os.listdir(item):
                            if not re.match('.*\.rpm$', package):
                                juicer.utils.Log.log_info('{0} is not an rpm. skipping!'.format(package))
                                continue

                            full_path = item + package

                            rpm_id = self._upload_rpm(full_path, env)
                            self._include_rpm_in_repo(rpm_id, env, repoid)

                    # https://path.to/package.rpm
                    elif re.match('https?://.*', item):
                        # download item and upload
                        if not re.match('.*\.rpm', item):
                            raise TypeError('{0} is not an rpm'.format(item))

                        filename = re.match('https?://.*/(.*\.rpm)', item).group(1)
                        remote = requests.get(item, env)

                        with open(filename, 'wb') as data:
                            data.write(remote.content())

                        rpm_id = self._upload_rpm(filename, env)
                        self._include_rpm_in_repo(rpm_id, env, repoid)

                        os.remove(filename)

                    else:
                        raise TypeError("what even is this?")

                self._generate_metadata(env, repoid)

        return output

    def publish(self, cart_name):
        """
        `cart_name` - Name of the release cart to publish

        Publishes a release cart to the pre-release environment.
        """
        juicer.utils.Log.log_debug("Initializing publish of cart '%s'" % cart_name)
        cart = juicer.common.Cart.Cart(cart_name, autoload=True)

        for repo, items in cart.iterrepos():
            juicer.utils.Log.log_debug("Initiating upload for repo '%s'" % repo)
            self.upload(items, [repo], [self._defaults['cart_dest']])

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

    def search_rpm(self, name='', envs=[], query='/packages/'):
        juicer.utils.Log.log_info('Packages:')

        for enviro in envs:
            # get list of all repos, then parse down to the ones we want
            _r = self.connectors[enviro].get(query)

            pkg_list = juicer.utils.load_json_str(_r.content)

            regex = re.compile("%s" % (name))

            for pkg in pkg_list:
                if _r.status_code != Constants.PULP_POST_OK:
                    _r.raise_for_status()

                if regex.search(pkg['name']):
                    juicer.utils.Log.log_info(pkg['name'])

    def hello(self, envs=[]):
        pass
