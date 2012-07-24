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
from juicer.common.Connectors import Connectors
from functools import wraps
import ConfigParser
import cStringIO
import fnmatch
import juicer.utils.Log
import juicer.utils.Remotes
import magic
import os
import os.path
import sys
import requests
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

def cart_repo_exists_p(name, connector, env):
    return repo_exists_p(name, connector, env)

def _config_file():
    """
    check that the config file is present and readable. if not,
    dump a template in place
    """
    config_file = os.path.expanduser('~/.juicer.conf')

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        return config_file
    elif os.path.exists(config_file) and not os.access(config_file, os.R_OK):
        raise IOError("Can not read %s" % config_file)
    else:
        config = ConfigParser.RawConfigParser({'username': 'user', \
                'password': 'pword', \
                'base_url': 'https://localhost/pulp/api/'}, \
                allow_no_value=True)
        config.add_section('qa')
        config.set('qa', 'base')
        config.set('qa', 'promotes_to', 'stage')
        config.add_section('stage')
        config.set('stage', 'requires_signature')
        config.set('stage', 'promotes_to', 'prod')
        config.add_section('prod')
        config.set('prod', 'requires_signature')

        with open(config_file, 'w') as conf:
            config.write(conf)

        raise Exception('default config file created')


def _config_test(config):
    """
    confirm the provided config has the required attributes and
    has a valid promotion path
    """
    required_keys = set(['username', 'password', 'base_url'])
    base_count = 0

    for section in config.sections():
        cfg = dict(config.items(section))

        if 'base' in cfg:
            base_count += 1

        # ensure required keys are present in each section
        if not required_keys.issubset(set(cfg.keys())):
            raise Exception("Missing values in config file: %s" % \
                            ", ".join(list(required_keys - set(cfg.keys()))))

        # ensure promotion path exists
        if 'promotes_to' in cfg and cfg['promotes_to'] not in config.sections():
            raise Exception("promotion_path: %s is not a config section" \
                    % cfg['promotes_to'])

    if base_count != 1:
        raise Exception("there must be one and only one base section")


def get_login_info():
    """
    Give back an array of dicts with the connection
    information for all the environments.
    """
    config = ConfigParser.SafeConfigParser(allow_no_value=True)
    connections = {}
    _defaults = {}
    _defaults['cart_dest'] = ''

    config.read(_config_file())

    _config_test(config)

    juicer.utils.Log.log_debug("Loading connection information:")
    for section in config.sections():
        cfg = dict(config.items(section))

        connections[section] = Connectors(cfg)

        if 'base' in cfg:
            _defaults['cart_dest'] = section

        juicer.utils.Log.log_debug("[%s] username: %s, base_url: %s" % \
                                       (section, \
                                            cfg['username'], \
                                            cfg['base_url']))

    _defaults['environments'] = config.sections()

    return (connections, _defaults)


def get_environments():
    """
    Return defined environments from config file for default
    environment values.
    """
    config = ConfigParser.SafeConfigParser(allow_no_value=True)

    config.read(_config_file())

    juicer.utils.Log.log_debug("Reading environment sections:")

    environments = config.sections()

    juicer.utils.Log.log_notice("Read environment sections: %s", environments)
    return environments


def user_exists_p(login, connector):
    """
    Determine if user exists in specified environment.
    """
    url = '/users/' + login + '/'
    _r = connector.get(url)
    return (_r.status_code == Constants.PULP_GET_OK)


def repo_exists_p(repo, connector, env):
    url = '/repositories/' + repo + '-' + env + '/'
    _r = connector.get(url)
    return (_r.status_code == Constants.PULP_GET_OK)


def role_exists_p(role, connector):
    url = '/roles/' + role + '/'
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


def dedupe(l):
    """
    Remove duplicates from a list.
    """
    return list(set(l))


def find_pattern(search_base, pattern='*.rpm'):
    """
    `search_base` - The directory to begin walking down.
    `pattern` - File pattern to match for.

    This is a generator which yields the full path to files (one at a
    time) which match the given glob (`pattern`).
    """
    # Stolen from http://rosettacode.org/wiki/Walk_a_directory/Recursively#Python
    if (not os.path.isdir(search_base)) and os.path.exists(search_base):
        # Adapt the algorithm to gracefully handle non-directory search paths
        yield search_base
    else:
        for root, dirs, files in os.walk(search_base):
            for filename in fnmatch.filter(files, pattern):
                yield os.path.join(root, filename)


def filter_package_list(package_list):
    """
    Filter a list of packages into local and remotes.
    """
    remote_pkgs = []
    local_pkgs = []

    possible_remotes = filter(lambda i: not os.path.exists(i), package_list)
    juicer.utils.Log.log_debug("Considering %s possible remotes" % len(possible_remotes))

    for item in possible_remotes:
        remote_pkgs.extend(juicer.utils.Remotes.assemble_remotes(item))
    juicer.utils.Log.log_notice("Remote packages: %s" % str(remote_pkgs))

    possible_locals = filter(os.path.exists, package_list)
    juicer.utils.Log.log_debug("Considering %s possible locals" % len(possible_locals))

    for item in possible_locals:
        for match in find_pattern(item):
            local_pkgs.append(match)
    juicer.utils.Log.log_notice("Local packages: %s" % str(local_pkgs))

    filtered_package_list = dedupe(remote_pkgs + local_pkgs)
    return filtered_package_list


def mute(returns_output=False):
    """
    `returns_output` - Returns all print output in a list.

    Capture or ignore all print output generated by a function.

    Usage:

    output = mute(returns_output=True)(module.my_func)(args)

    """
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


def is_rpm(path):
    """
    Use the python 'magic' library to find the type of file we're
    dealing with.
    """
    rpm_types = [Constants.MAGIC_RPM_BIN, Constants.MAGIC_RPM_NOARCH_BIN, Constants.MAGIC_RPM_SRC]
    m = magic.open(magic.NONE)
    m.load()

    path_type = m.file(path)

    if path_type in rpm_types:
        return True
    else:
        return False


def save_url_as(url, save_as):
    """
    Download the file `url` and save it to the local disk as
    `save_as`.
    """
    remote = requests.get(url)

    with open(save_as, 'wb') as data:
        data.write(remote.content)

def remote_url(connector, env, repo, filename):
    """
    return a str containing a link to the rpm in the pulp repository
    """
    dl_base = connector.base_url.replace('/pulp/api', '/pulp/repos')

    repoid = '%s-%s' % (repo, env)

    _r = connector.get('/repositories/%s/' % repoid)
    if not _r.status_code == Constants.PULP_GET_OK:
        juicer.utils.Log.log_error("%s is was not found as a repoid. Status code %s returned by pulp" % \
                (repoid, _r.status_code))
        exit(1)

    repo = juicer.utils.load_json_str(_r.content)['name']

    link = '%s/%s/%s/%s' % (dl_base, env, repo, filename)

    return link
