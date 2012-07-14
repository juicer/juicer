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
from juicer.common.JuicerCommon import JuicerCommon as jc
from functools import wraps
import ConfigParser
import cStringIO
import fnmatch
import juicer.utils.Log
import os
import os.path
import sys
try:
    import json
    json
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
    _defaults = {}

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        config.read(config_file)
    else:
        raise IOError("Can not read %s" % config_file)

    juicer.utils.Log.log_debug("Loading connection information:")
    for section in config.sections():
        cfg = dict(config.items(section))

        if not required_keys == set(cfg.keys()):
            raise Exception("Missing values in config file: %s" % \
                            ", ".join(list(required_keys - set(cfg.keys()))))

        juicer.utils.Log.log_debug("    [%s] username: %s, base_url: %s" % \
                                       (section, \
                                            cfg['username'], \
                                            cfg['base_url']))
        connections[section] = jc(cfg)

    _defaults['environments'] = config.sections()
    _defaults['cart_dest'] = config.sections()[0]

    return (connections, _defaults)


def get_environments():
    """
    Return defined environments from config file for default
    environment values.
    """
    config = ConfigParser.SafeConfigParser()
    config_file = os.path.expanduser('~/.juicer.conf')

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        config.read(config_file)
    else:
        raise IOError("Can not read %s" % config_file)

    juicer.utils.Log.log_debug("Reading environment sections:")

    environments = config.sections()
    return environments


def user_exists_p(args, connector):
    """
    Determine if user exists in specified environment.
    """
    url = '/users/' + args.login + '/'
    _r = connector.get(url)
    return (_r.status_code == Constants.PULP_GET_OK)


def repo_exists_p(args, connector, env):
    url = '/repositories/' + args.name + '-' + env + '/'
    _r = connector.get(url)
    return (_r.status_code == Constants.PULP_GET_OK)


def role_exists_p(args, connector):
    url = '/roles/' + args.role + '/'
    _r = connector.get(url)
    return (_r.status_code == Constants.PULP_GET_OK)


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


def write_json_document(title, body):
    """
    `title` - Name of the file to write.
    `body` - Python datastructure representing the document.

    This method handles transforming the body into a proper json
    string, and then writing the file to disk.
    """
    if not title.endswith('.json'):
        title += '.json'

    json_body = create_json_str(body)

    if os.path.exists(title):
        juicer.utils.Log.log_warn("Cart file '%s' already exists, overwriting with new data." % title)

    f = open(title, 'w')
    f.write(json_body)
    f.flush()
    f.close()


def read_json_document(title):
    """
    Reads in a json document and returns a native python
    datastructure.
    """
    if not title.endswith('.json'):
        juicer.utils.Log.log_warn("File name (%s) does not end with '.json', appending it automatically." % title)
        title += '.json'

    if not os.path.exists(title):
        raise IOError("Could not find file: '%s'" % title)

    f = open(title, 'r')
    doc = f.read()
    f.close()

    return load_json_str(doc)


def find_pattern(search_base, pattern='*.rpm'):
    """
    `search_base` - The directory to begin walking down.
    `pattern` - File pattern to match for.

    This is a generator which yields the full path to files (one at a
    time) which match the given glob (`pattern`).
    """
    # Stolen from http://rosettacode.org/wiki/Walk_a_directory/Recursively#Python
    if not os.path.isdir(search_base):
        # Adapt the algorithm to gracefully handle non-directory search paths
        yield search_base
    else:
        for root, dirs, files in os.walk(search_base):
            for filename in fnmatch.filter(files, pattern):
                yield os.path.join(root, filename)


def dedupe(l):
    """
    Remove duplicates from a list.
    """
    return list(set(l))


def filter_package_list():
    pass


def mute(returns_output=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            saved_stdout = sys.stdout
            sys.stdout = cStringIO.StringIO()
            try:
                out = func(*args, **kwargs)
                if returns_output:
                    out = sys.stdout.getvalue().strip().split()
            finally:
                sys.stdout = saved_stdout
            return out
        return wrapper
    return decorator
