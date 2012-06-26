# -*- coding: utf-8 -*-
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
                    data = {'regex':name,
                            'repoid':repo['id']}

                    _r = self.connectors[enviro].post(query, data)

                    if _r.status_code != 200:
                        _r.raise_for_status

                    for pkg in juicer.utils.load_json_string(_r.content):
                        output.append(pkg['filename'])
                        output.append(repo['id'])

        return output
