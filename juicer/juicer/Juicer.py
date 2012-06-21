# -*- coding: utf-8 -*-
import juicer.common
import juicer.utils
import juicer.juicer
import json
import requests
import simplejson
import re

class Juicer(object):
    def __init__(self, args):
        self.args = args

        connect_params = juicer.utils.get_login_info(self.args)

        self.jc = juicer.common.JuicerCommon(connect_params)

    def search_cart(self, query='/services/search/cart', output=[]):
        pass

    def search_rpm(self, name='', envs=[], query='/services/search/packages/', output=[]):
        output.append('Packages:')

        # if no envs listed, check all repositories
        if envs == None:
            data = {'regex':name}

            _r = self.jc.post(query, data)

            if _r.status_code != 200:
                _r.raise_for_status

            for pkg in simplejson.loads(str(_r.content)):
                output.append(pkg['filename'])

            return output
        else:
            output.append('Repository:')

            # get list of all repos, then parse down to the ones we want
            url = self.base_url + '/repositories/'
            _r = self.get(query)

            repo_list = simplejson.loads(str(_r.content))

            for repo in repo_list:
                for enviro in envs:
                    if re.match(".*-{0}$".format(enviro), repo['id']):
                        data = {'regex':name,
                                'repoid':repo['id']}
                        url = self.base_url + query

                        _r = self.jc.post(url, data)

                        if _r.status_code != 200:
                            _r.raise_for_status

                        for pkg in simplejson.loads(str(_r.content)):
                            output.append(pkg['filename'])
                            output.append(repo['id'])

            return output
