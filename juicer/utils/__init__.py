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
from juicer.common.Errors import *
from functools import wraps
from juicer.utils.ProgressBar import ProgressBar
import ConfigParser
import cStringIO
import fnmatch
import juicer.utils.Log
import juicer.utils.Remotes
import os
import os.path
import rpm
import hashlib
import sys
import requests
import shutil
import re
import urllib2
import yaml
try:
    import json
    json
except ImportError:
    import simplejson as json
from pymongo import Connection as MongoClient


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


def _system_config_file():
    """
    Check that the config file is present and readable. If not,
    copy a template in place.
    """
    config_file = Constants.SYSTEM_CONFIG

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        return config_file
    elif os.path.exists(config_file) and not os.access(config_file, os.R_OK):
        raise IOError("Can not read %s" % config_file)
    else:
        shutil.copy(Constants.EXAMPLE_SYSTEM_CONFIG, config_file)

        raise JuicerConfigError("Default config file created.\nCheck man 5 juicer.conf.")


def _user_config_file():
    """
    Check that the config file is present and readable. If not,
    copy a template in place.
    """
    config_file = Constants.USER_CONFIG

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        return config_file
    elif os.path.exists(config_file) and not os.access(config_file, os.R_OK):
        raise IOError("Can not read %s" % config_file)
    else:
        shutil.copy(Constants.EXAMPLE_USER_CONFIG, config_file)

        raise JuicerConfigError("Default config file created.\nCheck man 5 juicer.conf.")


def _config_file():
    """
    combine the user config file with the system config file (if present)
    """
    config = ConfigParser.SafeConfigParser()
    configs = []

    try:
        configs.append(_system_config_file())
    except Exception, e:
        juicer.utils.Log.log_debug(e)

    try:
        configs.append(_user_config_file())
    except Exception, e:
        juicer.utils.Log.log_debug(e)

    config.read(configs)
    return config


def _config_test(config):
    """
    confirm the provided config has the required attributes and
    has a valid promotion path
    """
    required_keys = set(['username', 'password', 'base_url', 'start_in', 'cart_host'])

    for section in config.sections():
        cfg = dict(config.items(section))

        # ensure required keys are present in each section
        if not required_keys.issubset(set(cfg.keys())):
            raise JuicerConfigError("Missing values in config file: %s" % \
                                ", ".join(list(required_keys - set(cfg.keys()))))

        # ensure promotion path exists
        if 'promotes_to' in cfg and cfg['promotes_to'] not in config.sections():
            raise JuicerConfigError("promotion_path: %s is not a config section" \
                                % cfg['promotes_to'])


def cart_db():
    """
    return a pymongo db connection for interacting with cart objects
    """
    config = _config_file()
    _config_test(config)

    juicer.utils.Log.log_debug("Establishing cart connection:")
    cart_con = MongoClient(dict(config.items(config.sections()[0]))['cart_host'])
    cart_db = cart_con.carts

    return cart_db


def upload_cart(cart, collection):
    """
    Connect to mongo and store your cart in the specified collection.
    """
    cart_cols = cart_db()

    cart_json = read_json_document(cart.cart_file())
    cart_id = cart_cols[collection].save(cart_json)

    cart.save()

    return cart_id


def get_login_info():
    """
    Give back an array of dicts with the connection
    information for all the environments.
    """
    connections = {}
    _defaults = {}
    _defaults['start_in'] = ''
    _defaults['rpm_sign_plugin'] = ''

    config = _config_file()

    _config_test(config)

    juicer.utils.Log.log_debug("Loading connection information:")
    for section in config.sections():
        cfg = dict(config.items(section))

        connections[section] = Connectors(cfg)

        if 'start_in' in cfg:
            _defaults['start_in'] = cfg['start_in']

        if 'rpm_sign_plugin' in cfg:
            _defaults['rpm_sign_plugin'] = cfg['rpm_sign_plugin']

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
    config = ConfigParser.SafeConfigParser()

    config = _config_file()

    juicer.utils.Log.log_debug("Reading environment sections:")

    environments = config.sections()

    juicer.utils.Log.log_notice("Read environment sections: %s", environments)
    return environments


def get_next_environment(env):
    """
    Given an environment, return the next environment in the
    promotion hierarchy
    """
    config = _config_file()

    juicer.utils.Log.log_debug("Finding next environment...")

    if env not in config.sections():
        raise JuicerConfigError("%s is not a server configured in juicer.conf" % env)

    section = dict(config.items(env))

    return section['promotes_to']


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
    Attempt to validate the path as an actual (S)RPM. If an exception
    is raised then this is not an RPM.
    """

    try:
        ts = rpm.TransactionSet()
        fd = os.open(path, os.O_RDONLY)
        ts.hdrFromFdno(fd)
        os.close(fd)
        return True
    except:
        return False


def is_remote_rpm(item):
    """
    Attempt to determine if the item given is a url to an rpm and
    as such, would need to be downloaded.
    """

    return re.match(r'http(?:s)?://.*\.rpm', item)


def save_url_as(url, save_as):
    """
    Download the file `url` and save it to the local disk as
    `save_as`.
    """

    remote = requests.get(url, verify=False)

    if not remote.status_code == Constants.PULP_GET_OK:
        raise JuicerPulpError("A %s error occurred trying to get %s" %
                                   (remote.status_code, url))

    with open(save_as, 'wb') as data:
        data.write(remote.content)


def remote_url(connector, env, repo, filename):
    """
    return a str containing a link to the rpm in the pulp repository
    """
    dl_base = connector.base_url.replace('/pulp/api/v2', '/pulp/repos')

    repoid = '%s-%s' % (repo, env)

    _r = connector.get('/repositories/%s/' % repoid)
    if not _r.status_code == Constants.PULP_GET_OK:
        # maybe the repo name is the repoid
        _r = connector.get('/repositories/%s/' % repo)
        if not _r.status_code == Constants.PULP_GET_OK:
            raise JuicerPulpError("%s is was not found as a repoid. Status code %s returned by pulp" % \
                    (repoid, _r.status_code))

    repo = juicer.utils.load_json_str(_r.content)['display_name']

    link = '%s/%s/%s/%s' % (dl_base, env, repo, filename)

    return link


def rpms_signed_p(rpm_files=None):
    """
    Are these RPMs signed?
    """
    return all([check_sig(rpm_file) for rpm_file in rpm_files])


def return_hdr(ts, package):
    """
    Hand back the hdr - duh - if the pkg is foobar handback None

    Shamelessly stolen from Seth Vidal
    http://yum.baseurl.org/download/misc/checksig.py
    """
    try:
        fdno = os.open(package, os.O_RDONLY)
    except OSError:
        hdr = None
        return hdr
    ts.setVSFlags(~(rpm.RPMVSF_NOMD5 | rpm.RPMVSF_NEEDPAYLOAD))
    try:
        hdr = ts.hdrFromFdno(fdno)
    except rpm.error:
        hdr = None
        raise rpm.error
    if type(hdr) != rpm.hdr:
        hdr = None
    ts.setVSFlags(0)
    os.close(fdno)
    return hdr


def get_sig_info(hdr):
    """
    hand back signature information and an error code

    Shamelessly stolen from Seth Vidal
    http://yum.baseurl.org/download/misc/checksig.py
    """
    string = '%|DSAHEADER?{%{DSAHEADER:pgpsig}}:{%|RSAHEADER?{%{RSAHEADER:pgpsig}}:{%|SIGGPG?{%{SIGGPG:pgpsig}}:{%|SIGPGP?{%{SIGPGP:pgpsig}}:{(none)}|}|}|}|'
    siginfo = hdr.sprintf(string)
    if siginfo != '(none)':
        error = 0
        sigtype, sigdate, sigid = siginfo.split(',')
    else:
        error = 101
        sigtype = 'MD5'
        sigdate = 'None'
        sigid = 'None'

    infotuple = (sigtype, sigdate, sigid)
    return error, infotuple


def check_sig(package):
    """
    check if rpm has a signature, we don't care if it's valid or not
    at the moment

    Shamelessly stolen from Seth Vidal
    http://yum.baseurl.org/download/misc/checksig.py
    """
    rpmroot = '/'

    ts = rpm.TransactionSet(rpmroot)

    sigerror = 0
    ts.setVSFlags(0)
    hdr = return_hdr(ts, package)
    sigerror, (sigtype, sigdate, sigid) = get_sig_info(hdr)
    if sigid == 'None':
        keyid = 'None'
    else:
        keyid = sigid[-8:]
    if keyid != 'None':
        return True
    else:
        return False


def parse_manifest(manifest):
    """
    return a list of dicts containing an rpm name, version and release
    eg: [{'name': 'httpd', 'version': 1.3.39, 'release': 1}]
    """
    regex = re.compile('(.*)-(.*)')
    manifest = os.path.expanduser(manifest)

    if not os.path.exists(manifest):
        raise JuicerManifestError('File not found: %s' % manifest)

    rpm_list = []
    fd = open(manifest)
    data = yaml.load(fd)

    if data == None:
        raise JuicerManifestError('%s contains no items' % manifest)

    for name, version in data.iteritems():
        if version == 'absent':
            juicer.utils.Log.log_debug('%s is absent. Skipping...' % name)
        else:
            try:
                _m = regex.match(version)
                version = _m.group(1)
                release = _m.group(2)
                rpm_list.append({'name': name, 'version': _m.group(1), 'release': _m.group(2)})
                juicer.utils.Log.log_debug('Adding %s version %s release %s' % (name, version, release))
            except:
                raise JuicerManifestError('The manifest %s is improperly formatted' % manifest)
                return False

    return rpm_list


def rpm_info(rpm_path):
    """
    Query information about the RPM at `rpm_path`.

    TODO: Remove the duplication of code from upload_rpm() below.
    """
    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
    rpm_info = {}

    rpm_fd = open(rpm_path, 'rb')
    pkg = ts.hdrFromFdno(rpm_fd)
    rpm_info['name'] = pkg['name']
    rpm_info['version'] = pkg['version']
    rpm_info['release'] = pkg['release']
    rpm_info['epoch'] = 0
    rpm_info['arch'] = pkg['arch']
    rpm_info['nvrea'] = tuple((rpm_info['name'], rpm_info['version'], rpm_info['release'], rpm_info['epoch'], rpm_info['arch']))
    rpm_info['cksum'] = hashlib.md5(rpm_path).hexdigest()
    rpm_info['size'] = os.path.getsize(rpm_path)
    rpm_info['package_basename'] = os.path.basename(rpm_path)
    rpm_fd.close()
    return rpm_info


def upload_rpm(rpm_path, repoid, connector):
    """
    upload an rpm into pulp

    rpm_path: path to an rpm
    connector: the connector to use for interacting with pulp
    """
    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)

    rpm_fd = open(rpm_path, 'rb')
    pkg = ts.hdrFromFdno(rpm_fd)
    name = pkg['name']
    version = pkg['version']
    release = pkg['release']
    epoch = 0
    arch = pkg['arch']
    nvrea = tuple((name, version, release, epoch, arch))
    cksum = hashlib.md5(rpm_path).hexdigest()
    size = os.path.getsize(rpm_path)
    package_basename = os.path.basename(rpm_path)

    juicer.utils.Log.log_notice("Expected amount to seek: %s (package size by os.path.getsize)" % size)

    # initiate upload
    upload = juicer.utils.Upload.Upload(package_basename, cksum, size, repoid, connector)

    #create a statusbar
    pbar = ProgressBar(size)

    # read in rpm
    upload_flag = False
    total_seeked = 0
    rpm_fd.seek(0)
    while total_seeked < size:
        rpm_data = rpm_fd.read(Constants.UPLOAD_AT_ONCE)
        last_offset = total_seeked
        total_seeked += len(rpm_data)
        juicer.utils.Log.log_notice("Seeked %s data... (total seeked: %s)" % (len(rpm_data), total_seeked))
        upload_code = upload.append(fdata=rpm_data, offset=last_offset)
        if upload_code != Constants.PULP_PUT_OK:
            juicer.utils.Log.log_error("Upload failed.")
        pbar.update(len(rpm_data))
    pbar.finish()
    rpm_fd.close()

    juicer.utils.Log.log_notice("Seeked total data: %s" % total_seeked)

    # finalize upload
    rpm_id = upload.import_upload(nvrea=nvrea, rpm_name=name)

    juicer.utils.Log.log_debug("RPM upload complete. New 'packageid': %s" % rpm_id)

    # clean up working dir
    upload.clean_upload()
    return rpm_id


def get_cart(base_url, env, cart_name):
    """
    returns a dict object representing a cart stored in pulp

    base_url: a str for the base_url (eg: http://sweet.pulp.repo/pulp/api/)
    env: a str with the the name of the environement (eg: prod)
    cart_name: a str with the name of the cart to get
    """
    base_url = base_url.replace('/pulp/api/', '/pulp/repos')
    url = '%s/%s/carts/%s.json' % (base_url, env, cart_name)

    rsock = urllib2.urlopen(url)
    data = rsock.read()
    rsock.close()

    return load_json_str(data)
