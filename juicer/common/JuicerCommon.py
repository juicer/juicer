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
import requests

class JuicerCommon(object):
    def __init__(self, connect_params):
        self.base_url = connect_params['base_url']
        self.auth = (connect_params['username'], connect_params['password'])
        self.headers = {'content-type': 'application/json'}

    def delete(self, url=""):
        url = self.base_url + url
        return requests.delete(url, auth=self.auth, headers=self.headers,
                               verify=False)

    def get(self, url=""):
        url = self.base_url + url
        return requests.get(url, auth=self.auth, headers=self.headers,
                            verify=False)

    def post(self, url="", data={}):
        url = self.base_url + url
        return requests.post(url, juicer.utils.create_json_str(data), auth=self.auth,
                             headers=self.headers, verify=False)

    def put(self, url="", data={}):
        url = self.base_url + url
        return requests.put(url, juicer.utils.create_json_str(data), auth=self.auth,
                            headers=self.headers, verify=False)
