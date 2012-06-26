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

import ConfigParser
import juicer.common
import sys
import os
try:
    import json
except ImportError:
    import simplejson as json

def load_json_str(jstr):
    """
    Internalize the json content object (`jstr`) into a native Python
    datastructure and return it.
    """
    return json.loads(str(jstr))

def create_json_str(input_ds):
    """
    Load a native Python datastructure into a json formatted string
    and return it.
    """
    return json.dumps(input_ds)

def get_login_info():
    """
    Give back an array of dicts with the connection
    information for all the environments.
    """
    config = ConfigParser.SafeConfigParser()
    config_file = os.path.expanduser('~/.juicer.conf')
    required_keys = set(['username', 'password', 'base_url'])
    connections = {}

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        config.read(config_file)
    else:
        raise IOError("Can not read %s" % config_file)

    for section in config.sections():
        cfg = dict(config.items(section))

        if not required_keys == set(cfg.keys()):
            raise Exception("Missing values in config file: %s" % \
                                ", ".join(list(required_keys - set(cfg.keys()))))

        connections[section] = juicer.common.JuicerCommon(cfg)

    return connections

def user_exists_p(args, connector):
    """
    Determine if user exists in specified environment.
    """
    url = '/users/' + args.login + '/'
    _r = connector.get(url)
    return (_r.status_code == 200)

def role_exists_p(args, connector):
    url = connector.base_url + '/roles/' + args.role + '/'
    _r = connector.get(url)
    return (_r.status_code == 200)

def flatten(x):
    """
    Flatten an arbitrary depth nested list.
    """
    # Lifted from: http://stackoverflow.com/a/406822/263969
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def print_stderr(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()
