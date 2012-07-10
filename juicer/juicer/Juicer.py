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
import juicer.juicer
import juicer.utils
import re
import os
import rpm
import hashlib
import requests


class Juicer(object):
    def __init__(self, args):
        self.args = args

        self.connectors = juicer.utils.get_login_info()

    # starts the 3-step upload process
    def _init_up(self, query='/services/upload/', name='', cksum='', size='', \
            env='re'):
        data = {'name': name,
                'checksum': cksum,
                'size': size}

        _r = self.connectors[env].post(query, data)
        uid = juicer.utils.load_json_str(_r.content)['id']

        return uid

    # continues 3-step upload process. this is where actual data transfer
    # occurs!
    def _append_up(self, query='/services/upload/append/', uid='', fdata='', \
                    env='re'):
        uri = query + uid + '/'
        data = {'file-id': uid,
                'file-data': fdata.decode('utf-8', 'replace')}

        _r = self.connectors[env].put(uri, data)

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

        return juicer.utils.load_json_str(_r.content)

    # provides a simple interface for the pulp upload API
    def _upload_rpm(self, package):
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

        # initiate uploade
        upload_id = self._init_up(name=name, cksum=cksum, size=size)

        # read in rpm
        while True:
            rpm_data = rpm_fd.read(10485760)

            if not rpm_data:
                break

            upload_flag = self._append_up(uid=upload_id, fdata=rpm_data)

        # finalize upload
        if upload_flag == True:
            code = self._import_up(uid=upload_id, name=name, cksum=cksum, \
                nvrea=nvrea, size=size)

        rpm_fd.close()

    # this is used to upload files to pulp
    def upload(self, items=[], repos=[], envs=[], output=[]):
        if envs == None:
            envs = ['re']

        for item in items:
            # path/to/package.rpm
            if os.path.isfile(item):
                # process individual file
                if not re.match('.*\.rpm', item):
                    raise TypeError("{0} is not an rpm".format(item))

                self._upload_rpm(item)

            # path/to/packages/
            elif os.path.isdir(item):
                # process files in dir
                for package in os.listdir(item):
                    if not re.match('.*\.rpm$', package):
                        output.append('{0} is not an rpm. skipping!'.format(
                            package))
                        continue

                    full_path = item + package

                    self._upload_rpm(full_path)

            # https://path.to/package.rpm
            elif re.match('https?://.*', item):
                # download item and upload
                if not re.match('.*\.rpm', item):
                    raise TypeError('{0} is not an rpm'.format(item))

                filename = re.match('https?://.*/(.*\.rpm)', item).group(1)
                remote = requests.get(item)

                with open(filename, 'wb') as data:
                    data.write(remote.content())

                self._upload_rpm(filename)

                os.remove(filename)

            else:
                raise TypeError("what even is this?")

        return output

    def create(self, cart_name, payload, output=[]):
        """
        `name` - Name of this release cart
        `payload` - list of ['reponame', item1, ..., itemN] lists
        """
        output.append("Creating cart " + cart_name)
        repo_items_hash = {}

        for repo_items in payload:
            repo = repo_items[0]
            rpms = repo_items[1:]
            repo_items_hash[repo] = rpms

        output.append(repo_items_hash)
        output.append("Writing cart to disk: %s.json" % cart_name)

        juicer.utils.write_json_document(cart_name + ".json", repo_items_hash)

        return output

    def show(self, cart_name, output=[]):
        cart_body = juicer.utils.read_json_document(cart_name + '.json')

        for repo, items in cart_body.iteritems():
            output.append(repo.upper())
            # Underline the repo name
            output.append("-" * len(repo))
            # Add all the RPMs
            output.extend(items)
            output.append('')

        print "\n".join(output)

    def search_cart(self, query='/services/search/cart', output=[]):
        pass

    def search_rpm(self, name='', envs=[], \
            query='/packages/', output=[]):
        output.append('Packages:')

        # if no envs listed, check all repositories
        if envs == None:
            envs = ['re', 'qa', 'stage', 'prod']

        for enviro in envs:
            # get list of all repos, then parse down to the ones we want
            _r = self.connectors[enviro].get(query)

            pkg_list = juicer.utils.load_json_str(_r.content)

            regex = re.compile("%s" % (name))

            for pkg in pkg_list:
                if _r.status_code != Constants.PULP_POST_OK:
                    _r.raise_for_status()

                if regex.search(pkg['name']):
                    output.append(pkg['name'])

        return output

    def hello(self, envs=[], output=[]):
        pass
