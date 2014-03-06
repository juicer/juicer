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

import juicer.utils
from juicer.common import Constants


class Upload(object):
    def __init__(self, pkg_name, cksum, size, repoid, connector, query='/content/uploads/'):
        """
        in addition to creating an upload object, this
        initializes the upload of an rpm into pulp

        pkg_name: the name of the package to upload
        cksum: checksum of the rpm
        size: total size of the rpm
        connector: the connector for the environment to upload into
        """
        self.pkg_name = pkg_name
        self.connector = connector
        self.cksum = cksum
        self.size = size
        self.repoid = repoid

        _r = self.connector.post(query)
        if _r.status_code == Constants.PULP_POST_CREATED:
            self.uid = juicer.utils.load_json_str(_r.content)['upload_id']

            juicer.utils.Log.log_debug("Initialized upload process. POST returned with data: %s" % str(_r.content))
        else:
            _r.raise_for_status()

    def append(self, fdata, offset, query='/content/uploads'):
        """
        append binary data to an upload
        `fdata` - binary data to send to pulp
        `offset` - the amount of previously-uploaded data
        """
        query = '%s/%s/%s/' % (query, self.uid, offset)
        _r = self.connector.put(query, fdata, log_data=False, auto_create_json_str=False)

        juicer.utils.Log.log_notice("Appending to: %s" % query)
        juicer.utils.Log.log_debug("Continuing upload with append. POST returned with data: %s" % str(_r.content))

        return _r.status_code

    def import_upload(self, nvrea, ftype='rpm', rpm_name='', desc=None, htype='md5', lic=None, group=None, vendor=None, req=None):
        """
        import the completed upload into pulp
        `ftype` - the type of the upload
        `rpm_name` - the name of the uploaded rpm
        `desc` - description of the rpm
        `htype` - checksum type
        `lic` - license used in the packaged software
        `group` - package group
        `vendor` - software vendor
        `req` - dependencies
        """
        query = '/repositories/%s/actions/import_upload/' % self.repoid
        data = {'upload_id': self.uid,
                'unit_type_id': ftype,
                'unit_key': {
                    'name': rpm_name,
                    'version': nvrea[1],
                    'release': nvrea[2],
                    'epoch': nvrea[3],
                    'arch': nvrea[4],
                    'checksumtype': htype,
                    'checksum': self.cksum,
                    },
                'unit_metadata': {
                    'filename': self.pkg_name,
                    'license': lic if lic else '',
                    'requires': req if req else '',
                    #    'type': ftype,
                    'description': desc if desc else '',
                    #    'size': self.size,
                    'vendor': vendor if vendor else '',
                    'relativepath': self.pkg_name,
                    }
                }

        _r = self.connector.post(query, data)

        if _r.status_code not in [Constants.PULP_POST_OK, Constants.PULP_POST_ACCEPTED]:
            juicer.utils.Log.log_error("Import error importing '%s'... server said: \n %s", (self.pkg_name,
                                       juicer.utils.load_json_str(_r.content)))
            _r.raise_for_status()

        juicer.utils.Log.log_debug("Finalized upload id %s" % self.uid)

    def clean_upload(self, query='/content/uploads/'):
        """
        pulp leaves droppings if you don't specifically tell it
        to clean up after itself. use this to do so.
        """
        query = query + self.uid + '/'
        _r = self.connector.delete(query)

        if _r.status_code == Constants.PULP_DELETE_OK:
            juicer.utils.Log.log_info("Cleaned up after upload request.")
        else:
            _r.raise_for_status()
