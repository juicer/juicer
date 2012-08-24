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
from juicer.common import Constants


class Upload(object):
    def __init__(self, name, cksum, size, repoid, connector, query='/services/upload/'):
        """
        in addition to creating an upload object, this
        initializes the upload of an rpm into pulp
        
        name: the name of the package to upload
        cksum: checksum of the rpm
        size: total size of the rpm
        connector: the connector for the environment to upload into
        """
        self.name = name
        self.connector = connector
        self.cksum = cksum
        self.size = size
        self.repoid = repoid

        data = {'name': name,
                'checksum': cksum,
                'size': size}

        _r = self.connector.post(query, data)
        self.uid = juicer.utils.load_json_str(_r.content)['id']

        juicer.utils.Log.log_debug("Initialized upload process. POST returned with data: %s" % str(_r.    content))

    def _include_rpm_in_repo(self, pkgid):
        """
        includes an rpm in the designated repo
        """
        query = '/repositories/' + self.repoid + '/add_package/'
        data = {'repoid': self.repoid,
                'packageid': [pkgid]}

        _r = self.connector.post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
            self.connectors.delete('/packages/' + pkgid + '/')
            _r.raise_for_status()

    def _include_file_in_repo(self, fileid):
        """
        includes a file in the designated repo
        """
        query = '/repositories/' + self.repoid + '/add_file/'
        data = {'fileids': [fileid]}

        _r = self.connector.post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
            print juicer.utils.load_json_str(_r.content)
            #self.connector.delete('/files/' + fileid + '/')
            _r.raise_for_status()

    def _generate_metadata(self):
        """
        causes pulp to regenerate the metadata for the repository
        """
        query = '/repositories/' + self.repoid + '/generate_metadata/'

        _r = self.connector.post(query)

        juicer.utils.Log.log_debug("Attempted metadata update for repo: %s -> %s" % \
                                       (self.repoid, str(_r.content)))

        if _r.status_code == Constants.PULP_POST_CONFLICT:
            juicer.utils.Log.log_debug("Metadata update in %s already in progress...: " % \
                                           self.repoid)
            while _r.status_code == Constants.PULP_POST_CONFLICT:
                time.sleep(3)
                _r = self.connector.post(query)
        if not _r.status_code == Constants.PULP_POST_ACCEPTED:
            _r.raise_for_status()

    def append(self, fdata, query='/services/upload/append/'):
        uri = query + self.uid + '/'
        _r = self.connector.put(uri, fdata, log_data=False, auto_create_json_str=False)

        juicer.utils.Log.log_notice("Appending to: %s" % uri)
        juicer.utils.Log.log_debug("Continuing upload with append. PUT returned with data: %s" % str(_r.  content))

        return juicer.utils.load_json_str(_r.content)

    def finalize(self, nvrea, ftype='rpm', desc='', htype='md5', lic='',
            group='', vendor='', req='', query='/services/upload/import/'):

        data = {'uploadid': self.uid,
                'metadata': {
                    'type': ftype,
                    'checksum': self.cksum,
                    'description': desc,
                    'hashtype': htype,
                    'pkgname': self.name,
                    'nvrea': nvrea,
                    'size': self.size,
                    'license': lic,
                    'group': group,
                    'vendor': vendor,
                    'requires': req}}

        _r = self.connector.post(query, data)

        if not _r.status_code == Constants.PULP_POST_OK:
            juicer.utils.Log.log_debug("Import error importing '%s'... server said: \n %s", name,
                                       juicer.utils.load_json_str(_r.content))
            _r.raise_for_status()

        juicer.utils.Log.log_debug("Finalized upload with data: %s" % str(_r.content))
        juicer.utils.Log.log_debug(juicer.utils.load_json_str(_r.content))

        final_id = juicer.utils.load_json_str(_r.content)['id']

        if ftype == 'rpm':
            self._include_rpm_in_repo(final_id)
        elif ftype == 'file':
            self._include_file_in_repo(final_id)

        self._generate_metadata()

        return final_id

