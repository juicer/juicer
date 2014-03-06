# -*- coding: utf-8 -*-
# Copyright © 2008-2011, Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# This file is taken from the Nushus project <http://fedorahosted.org/nushus/>
"""
Functions for handling remote package resources
"""
from BeautifulSoup import BeautifulSoup as bs
from os.path import exists, expanduser
import re
import urllib2
import juicer.utils.Log

REMOTE_PKG_TYPE = 1
REMOTE_INDEX_TYPE = 2
REMOTE_INPUT_FILE_TYPE = 3


def assemble_remotes(resource):
    """
    Using the specified input resource, assemble a list of rpm URLS.

    This function will, when given a remote package url, directory
    index, or a combination of the two in a local input file, do all
    the work required to turn that input into a list of only remote
    package URLs.
    """
    resource_type = classify_resource_type(resource)

    if resource_type is None:
        juicer.utils.Log.log_debug("Could not classify or find the input resource.")
        return []
    elif resource_type == REMOTE_PKG_TYPE:
        return [resource]
    elif resource_type == REMOTE_INDEX_TYPE:
        return parse_directory_index(resource)
    elif resource_type == REMOTE_INPUT_FILE_TYPE:
        # Later on this could examine the excluded data for directory
        # indexes and iterate over those too.
        remote_packages, excluded_data = parse_input_file(resource)
        return remote_packages


def classify_resource_type(resource):
    """
    Determine if the specified resource is remote or local.

    We can handle three remote resource types from the command line,
    remote RPMs, directory indexes, and input files. They're
    classified by matching the following patterns:

    - Remote RPMS start with http[s] and end with .RPM
    - Directory indexes start with http[s] and don't end in .RPM
    - Input files don't match above, exist() on local filesystem
    """
    if is_remote_package(resource):
        juicer.utils.Log.log_debug("Classified %s as a remote package" % resource)
        return REMOTE_PKG_TYPE
    elif is_directory_index(resource):
        juicer.utils.Log.log_debug("Classified %s as a directory index" % resource)
        return REMOTE_INDEX_TYPE
    elif exists(expanduser(resource)):
        juicer.utils.Log.log_debug("Classified %s as an input file" % resource)
        return REMOTE_INPUT_FILE_TYPE
    else:
        juicer.utils.Log.log_debug("Classified %s as unclassifiable" % resource)
        return None


def is_remote_package(resource):
    """
    Classify the input resource as a remote RPM or not.
    """
    remote_regexp = re.compile(r"^https?://(.+).rpm$", re.I)
    result = remote_regexp.match(resource)

    if result is not None:
        juicer.utils.Log.log_debug("%s matches remote package regexp" % resource)
        return True
    else:
        juicer.utils.Log.log_debug("%s doesn't match remote package regexp" % resource)
        return False


def is_directory_index(resource):
    """
    Classify the input resource as a directory index or not.
    """
    remote_regexp = re.compile(r"^https?://(.+)/?$", re.I)
    result = remote_regexp.match(resource)

    if result is not None:
        juicer.utils.Log.log_debug("%s matches directory index regexp" % resource)
        return True
    else:
        juicer.utils.Log.log_debug("%s doesn't match directory index regexp" % resource)
        return False


def parse_input_file(resource):
    """
    Parse input file into remote packages and excluded data.

    In addition to garbage, excluded data includes directory indexes
    for the time being. This will be revisited after basic
    functionality has been fully implemented.
    """
    input_resource = open(resource, 'r').read()
    remotes_list = [url for url in input_resource.split()]

    juicer.utils.Log.log_debug("Input file parsed into: %s\n" % str(remotes_list))

    remote_packages = [pkg for pkg in remotes_list if is_remote_package(pkg) is True]
    juicer.utils.Log.log_debug("remote_packages filtered into %s\n" % str(remote_packages))

    excluded_data = [datum for datum in remotes_list if datum not in remote_packages]
    juicer.utils.Log.log_debug("excluded_data filtered into %s\n" % str(excluded_data))

    http_indexes = [index for index in excluded_data if is_directory_index(index)]
    remotes_from_indexes = reduce(lambda x, y: x + parse_directory_index(y), http_indexes, [])

    return (remote_packages + remotes_from_indexes, excluded_data)


def parse_directory_index(directory_index):
    """
    Retrieve a directory index and make a list of the RPMs listed.
    """
    # Normalize our URL style
    if not directory_index.endswith('/'):
        directory_index = directory_index + '/'

    site_index = urllib2.urlopen(directory_index)
    parsed_site_index = bs(site_index)
    rpm_link_tags = parsed_site_index.findAll('a', href=re.compile(r'.*rpm$'))

    # Only save the HREF attribute values from the links found
    rpm_names = [link['href'] for link in rpm_link_tags]

    # Join the index path with the discovered names so we only return complete paths
    remote_list = map(lambda end: "".join([directory_index, end]), rpm_names)

    return remote_list
