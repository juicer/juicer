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


class Juicer(object):
    def __init__(self, args):
        self.args = args

        self.connectors = juicer.utils.get_login_info()

    # starts the 3-step upload process
    def _init_up(self, query='/services/upload/', name='', cksum='', size='', \
            env='re'):
        data = {'name':name,
                'checksum':cksum,
                'size':size}

        _r = self.connectors[env].post(query, data)
        uid = juicer.utils.load_json_str(_r.content)['id']

        return uid
 
    # continues 3-step upload process. this is where actual data transfer
    # occurs!
    def _append_up(self, query='/services/upload/append/', uid='', fdata='', env='re'):
        uri = query + uid + '/'
        data = {'file-id':uid,
                'file-data':fdata}

        _r = self.connectors[env].put(uri, data)

        return juicer.utils.load_json_str(_r.content)

    # finalizes the 3-step upload process. this is where metadata is set
    def _import_up(self, query='/services/upload/import/', uid='', name='', ftype='rpm', \
            cksum='', htype='md5', nvrea='', size='', lic='', group='', vendor='', \
            req='', env='re'):
        data = {'uploadid':uid,
                'metadata':{
                    'type':ftype,
                    'checksum':cksum,
                    'hashtype':htype,
                    'pkgname':name,
                    'nvrea':nvrea,
                    'size':size,
                    'license':lic,
                    'group':group,
                    'vendor':vendor,
                    'requires':req}}

        _r = self.connectors[env].post(query, data)

        return juicer.utils.load_json_str(_r.content)

    # this is used to upload files to pulp
    def upload(self, items=[], repos=[], envs=[], output=[]):
        if envs == None:
            envs = ['re']

        ts = rpm.TransactionSet()

        for item in items:
            if os.path.isfile(item):
                # process individual file
                rpm_fd = open(item)
                pkg = ts.hdrFromFdno(rpm_fd)
                name = pkg['name']
                version = pkg['version']
                release = pkg['release']
                epoch = 0
                arch = pkg['arch']
                nvrea = tuple((name, version, release, epoch, arch))
                cksum = hashlib.md5(item).hexdigest()
                size = os.path.getsize(item)

                # initiate uploade
                upload_id = self._init_up(name=name, cksum=cksum, size=size)

                # read in rpm
                rpm_data = unicode(rpm_fd.readlines())
                upload_flag = self._append_up(uid=upload_id, fdata=rpm_data)

                # finalize upload
                if upload_flag == True:
                    code = self._import_up(uid=upload_id, name=name, cksum=cksum, \
                        nvrea=nvrea, size=size)

                rpm_fd.close()

            elif os.path.isdir(item):
                # process dir
                output.append('dir')
            elif re.match('https?://.*', item):
                # download item and upload
                output.append('url')
            else:
                # TODO raise an actual error
                output.append('No! Bad!')
                break

        return output

    def search_cart(self, query='/services/search/cart', output=[]):
        pass

    def search_rpm(self, name='', envs=[], \
            query='/services/search/packages/', output=[]):
        output.append('Packages:')
        output.append('Repository:')

        # if no envs listed, check all repositories
        if envs == None:
            envs = ['re', 'qa', 'stage', 'prod']

        for enviro in envs:
            # get list of all repos, then parse down to the ones we want
            _r = self.connectors[enviro].get('/repositories/')

            repo_list = juicer.utils.load_json_str(_r.content)

            for repo in repo_list:
                if re.match(".*-{0}$".format(enviro), repo['id']):
                    data = {'regex': name,
                            'repoid': repo['id']}

                    _r = self.connectors[enviro].post(query, data)

                    if _r.status_code != Constants.PULP_POST_OK:
                        _r.raise_for_status()

                    for pkg in juicer.utils.load_json_str(_r.content):
                        output.append(pkg['filename'])
                        output.append(repo['id'])

        return output
