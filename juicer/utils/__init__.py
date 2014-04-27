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


from juicer.common import Constants
from juicer.common.Connectors import Connectors
from juicer.common.Errors import *
from functools import wraps
from juicer.utils.ProgressBar import ProgressBar
import ConfigParser
import cStringIO
import datetime
import fnmatch
import juicer.utils.Log
import juicer.utils.Remotes
import juicer.common.Repo
import os
import os.path
import rpm
import hashlib
import sys
import requests
import shutil
import re
import texttable
import urllib2
import yaml
try:
    import json
except ImportError:
    import simplejson as json
from pymongo import Connection as MongoClient
from pymongo import errors as MongoErrors


def load_json_str(jstr):
    """
    Internalize the json content object (`jstr`) into a native Python
    datastructure and return it.
    """
    return json.loads(str(jstr))


def create_json_str(input_ds, **kwargs):
    """
    Load a native Python datastructure into a json formatted string
    and return it.
    """
    return json.dumps(input_ds, **kwargs)


def cart_repo_exists_p(name, connector, env):
    return repo_exists_p(name, connector, env)


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
    try:
        cart_id = cart_cols[collection].save(cart_json)
    except MongoErrors.AutoReconnect:
        raise JuicerConfigError("Error saving cart to `cart_host`. Ensure that this node is the master.")
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
    juicer.utils.Log.log_debug("Read environment sections: %s", ', '.join(environments))
    return environments


def env_same_host(env1, env2):
    """
    determine if two environments are on the same host. returns
    true or false
    """
    config = _config_file()

    h1 = dict(config.items(env1))['base_url']
    h2 = dict(config.items(env2))['base_url']

    return h1 == h2


def get_next_environment(env):
    """
    Given an environment, return the next environment in the
    promotion hierarchy
    """
    config = _config_file()

    juicer.utils.Log.log_debug("Finding next environment...")

    if env not in config.sections():
        raise JuicerConfigError("%s is not a server configured in juicer.conf", env)

    section = dict(config.items(env))

    if 'promotes_to' not in section.keys():
        err = "Environment `%s` has no entry for `promotes_to`\nCheck man 5 juicer.conf." % env
        raise JuicerConfigError(err)

    return section['promotes_to']


def pulp_repo_path(connection, repoid):
    """
    Given a connection and a repoid, return the url of the repository
    """
    dl_base = connection.base_url.replace('/pulp/api/v2', '/pulp/repos')
    _m = re.match('(.*)-(.*)', repoid)
    repo = _m.group(1)
    env = _m.group(2)

    return "%s/%s/%s" % (dl_base, env, repo)


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
    possible_locals = filter(is_rpm, possible_locals)
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

    import magic
    m = magic.open(magic.MAGIC_MIME)
    m.load()
    mime = m.file(path)
    # rpms or directories are cool
    if 'rpm' in mime or 'directory' in mime:
        return True
    else:
        juicer.utils.Log.log_info("error: File `%s` is not an rpm" % path)
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
            raise JuicerPulpError("%s was not found as a repoid. Status code %s returned by pulp" % \
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

    if data is None:
        raise JuicerManifestError('%s contains no items' % manifest)

    for pkg_name, version in data.iteritems():
        if version == 'absent' or version == 'purged':
            juicer.utils.Log.log_debug('%s is absent/purged. Skipping...' % pkg_name)
        elif version == 'latest':
            juicer.utils.Log.log_debug('%s is set to latest. Finding...' % pkg_name)
            lversion, release = juicer.utils.find_latest(pkg_name)
            if not lversion and not release:
                # package wasn't found in repo so don't add it to the list
                continue
            juicer.utils.Log.log_debug('Adding %s version %s release %s' % (pkg_name, lversion, release))
            rpm_list.append({'name': pkg_name, 'version': lversion, 'release': release})
        else:
            try:
                _m = regex.match(version)
                version = _m.group(1)
                release = _m.group(2)
                rpm_list.append({'name': pkg_name, 'version': _m.group(1), 'release': _m.group(2)})
                juicer.utils.Log.log_debug('Adding %s version %s release %s' % (pkg_name, version, release))
            except:
                raise JuicerManifestError('The manifest %s is improperly formatted' % manifest)
                return False

    return rpm_list


def rpm_info(rpm_path):
    """
    Query information about the RPM at `rpm_path`.

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


def upload_rpm(rpm_path, repoid, connector, callback=None):
    """upload an rpm into pulp

    rpm_path: path to an rpm
    connector: the connector to use for interacting with pulp

    callback: Optional callback to call after an RPM is
    uploaded. Callback should accept one argument, the name of the RPM
    which was uploaded
    """
    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)

    info = rpm_info(rpm_path)
    pkg_name = info['name']
    nvrea = info['nvrea']
    cksum = info['cksum']
    size = info['size']
    package_basename = info['package_basename']

    juicer.utils.Log.log_notice("Expected amount to seek: %s (package size by os.path.getsize)" % size)

    # initiate upload
    upload = juicer.utils.Upload.Upload(package_basename, cksum, size, repoid, connector)

    #create a statusbar
    pbar = ProgressBar(size)

    # read in rpm
    total_seeked = 0
    rpm_fd = open(rpm_path, 'rb')
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
    rpm_id = upload.import_upload(nvrea=nvrea, rpm_name=pkg_name)

    juicer.utils.Log.log_debug("RPM upload complete. New 'packageid': %s" % rpm_id)

    # clean up working dir
    upload.clean_upload()

    # Run callbacks?
    if callback:
        try:
            juicer.utils.Log.log_debug("Calling upload callack: %s" % str(callback))
            callback(pkg_name)
        except Exception:
            juicer.utils.Log.log_error("Exception raised in callback: %s", str(callback))
            pass

    return rpm_id


def download_cart(cart_name, env):
    """
    accesses mongodb and return a cart spec stored there
    """
    cart_con = cart_db()
    carts = cart_con[env]

    return carts.find_one({'_id': cart_name})


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


def search_carts(env, pkg_name, repos):
    """
    returns a list of carts containing a package with the specified name

    env: the name of an environment from the juicer config
    pkg_name: the name of the package for which to search
    repos: a list of repos in which to search for the package
    """
    db = cart_db()
    carts = db[env]

    for repo in repos:
        field = 'repos_items.%s' % repo
        value = '.*%s.*' % pkg_name

        found_carts = []

        for cart in carts.find({field: {'$regex': value}}):
            found_carts.append(cart)
        return found_carts


def find_latest(pkg_name, url='/content/units/rpm/search/'):
    """
    returns the highest version and release of the specified package found
    in the specified environment

    env: the juicer environment to search
    pkg_name: the name of the package for which to search
    """
    connectors, defaults = juicer.utils.get_login_info()
    connector = connectors[defaults['start_in']]
    # this data block is... yeah. searching in pulp v2 is painful
    #
    # https://pulp-dev-guide.readthedocs.org/en/latest/rest-api/content/retrieval.html#search-for-units
    # https://pulp-dev-guide.readthedocs.org/en/latest/rest-api/conventions/criteria.html#search-criteria
    #
    # those are the API docs for searching
    data = {
        'criteria': {
            'filters': {'name': pkg_name},
            'sort': [['version', 'descending'], ['release', 'descending']],
            'limit': 1,
            'fields': ['name', 'description', 'version', 'release', 'arch', 'filename']
        },
        'include_repos': 'true'
    }

    # search pulp for package
    _r = connector.post(url, data)
    if not _r.status_code == Constants.PULP_POST_OK:
        juicer.utils.Log.log_debug("Expected PULP_POST_OK, got %s", _r.status_code)
        _r.raise_for_status()
    content = juicer.utils.load_json_str(_r.content)
    if len(content) < 1:
        juicer.utils.Log.log_info("%s was not found in %s.", (pkg_name, defaults['start_in']))
        return False, False
    else:
        pkg_info = content[0]
        juicer.utils.Log.log_debug("found %s version %s" % (pkg_info['version'], pkg_info['release']))

        return pkg_info['version'], pkg_info['release']


def juicer_version():
    """
    Duh, just print out what version of juicer you're running.
    """
    return juicer.__version__


def header(msg):
    """
    Wrap `msg` in bars to create a header effect
    """
    # Accounting for '| ' and ' |'
    width = len(msg) + 4
    s = []
    s.append('-' * width)
    s.append("| %s |" % msg)
    s.append('-' * width)
    return '\n'.join(s)


def table(rows, columns=None):
    if not columns is None:
        t = texttable.Texttable(max_width=columns)
    else:
        t = texttable.Texttable()

    t.add_rows(rows)
    return t.draw()


def unique_repo_def_envs(repo_def):
    defined_envs = set()
    for repo in repo_def:
        defined_envs = defined_envs.union(repo['env'])
        juicer.utils.Log.log_debug("envs for repo %s: %s", repo['name'], ", ".join(repo['env']))
    return defined_envs


def repo_exists_in_repo_list(repo, repo_list):
    """`repo_def` - a Repo object representing a juicer repo def

    `repo_list` a list of repo names (sans environment-id), per the
    data from juicer.admin.JuicerAdmin.list_repos
    """
    return repo['name'] in repo_list


def repo_in_defined_envs(repo, all_envs):
    """Raises exception if the repo references undefined environments"""
    remaining_envs = set(repo['env']) - set(all_envs)
    if set(repo['env']) - set(all_envs):
        raise JuicerRepoInUndefinedEnvs("Repo def %s references undefined environments: %s" %
                                        (repo['name'], ", ".join(list(remaining_envs))))
    else:
        return True


def repo_def_matches_reality(juicer_def, pulp_def):
    """Compare a juicer repo def with a given pulp definition. Compute and
    return the update necessary to make `pulp_def` match `juicer_def`.

    `juicer_def` - A JuicerRepo() object representing a juicer repository
    `pulp_def` - A PulpRepo() object representing a pulp repository
    """
    return juicer.common.Repo.RepoDiff(juicer_repo=juicer_def, pulp_repo=pulp_def)


def exit_with_code(code):
    """Exit with a specific return code"""
    sys.exit(code)


def iso_date_str():
    return datetime.datetime.now().isoformat()


def chunk_list(l, n):
    """Return `n` size lists from a given list `l`"""
    return [l[i:i + n] for i in range(0, len(l), n)]


def debug_log_repo(repo):
    """Log to DEBUG level a Repo (or subclass) pretty-printed"""
    ds_str = juicer.utils.create_json_str(repo,
                                          indent=4,
                                          cls=juicer.common.Repo.RepoEncoder)
    juicer.utils.Log.log_debug(ds_str)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]
