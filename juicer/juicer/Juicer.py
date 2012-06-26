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
import juicer.juicer
import requests
import re

class Juicer(object):
    def __init__(self, args):
        self.args = args

        self.connectors = juicer.utils.get_login_info()

    def search_cart(self, query='/services/search/cart', output=[]):
        pass

    def search_rpm(self, name='', envs=[], query='/services/search/packages/', output=[]):
        output.append('Packages:')
        output.append('Repository:')

        # if no envs listed, check all repositories
        if envs == None:
            envs = ['re', 'qa', 'stage', 'prod']

        for enviro in envs:
            # get list of all repos, then parse down to the ones we want
            _r = self.connectors[enviro].get('/repositories/')

            repo_list = juicer.utils.load_json_string(_r.content)

            for repo in repo_list:
                if re.match(".*-{0}$".format(enviro), repo['id']):
                    data = {'regex': name,
                            'repoid': repo['id']}

                    _r = self.connectors[enviro].post(query, data)

                    if _r.status_code != 200:
                        _r.raise_for_status

                    for pkg in juicer.utils.load_json_string(_r.content):
                        output.append(pkg['filename'])
                        output.append(repo['id'])

        return output
