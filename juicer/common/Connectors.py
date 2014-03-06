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
from juicer.common.Errors import JuicerPulpError
import juicer.utils
import juicer.utils.Log
import requests


class Connectors(object):
    def __init__(self, connect_params):
        self.base_url = connect_params['base_url']
        self.auth = (connect_params['username'], connect_params['password'])
        self.headers = {'content-type': 'application/json'}
        if 'requires_signature' in connect_params:
            self.requires_signature = True
        else:
            self.requires_signature = False

    def delete(self, url=""):
        self.check_api_version()
        url = self.base_url + url
        juicer.utils.Log.log_debug("[REST:DELETE:%s]", url)

        return requests.delete(url, auth=self.auth, headers=self.headers,
                               verify=False)

    def get(self, url=""):
        self.check_api_version()
        url = self.base_url + url

        juicer.utils.Log.log_debug("[REST:GET:%s]", url)
        return requests.get(url, auth=self.auth, headers=self.headers,
                            verify=False)

    def post(self, url="", data={}, log_data=True, auto_create_json_str=True):
        self.check_api_version()
        url = self.base_url + url
        if log_data:
            juicer.utils.Log.log_debug("[REST:POST:%s] [Data:%s]", url, str(data))

        if auto_create_json_str:
            data = juicer.utils.create_json_str(data)

        return requests.post(url, data, \
                auth=self.auth, headers=self.headers, verify=False)

    def put(self, url="", data={}, log_data=True, auto_create_json_str=True):
        self.check_api_version()
        url = self.base_url + url
        if log_data:
            juicer.utils.Log.log_debug("[REST:PUT:%s] [Data:%s]", url, str(data))

        if auto_create_json_str:
            data = juicer.utils.create_json_str(data)

        return requests.put(url, data, \
                auth=self.auth, headers=self.headers, verify=False)

    def check_api_version(self):
        """
        Self check that the client expects the api version used by the
        server. /status/ is available without authentication so it
        will not interfere with hello.
        """
        url = self.base_url + "/status/"
        juicer.utils.Log.log_debug("[REST:GET:%s]", url)

        _r = requests.get(url, auth=self.auth, headers=self.headers,
                          verify=False)

        if _r.status_code == Constants.PULP_GET_OK:  # server is up, cool.
            version = juicer.utils.load_json_str(_r.content)['api_version'].strip()
            if version != Constants.EXPECTED_SERVER_VERSION:  # we done goofed
                raise JuicerPulpError("Client expects %s and got %s -- you should probably update!" \
                                      % (Constants.EXPECTED_SERVER_VERSION, version))
        return True
