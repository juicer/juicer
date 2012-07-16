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
import os
import re
import urllib2


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
#    if options.verbosity > 1:
#       sys.stderr.write("remotes.py[assemble_remotes(): \
# Attempting to classify %s as a resource type.\n" % resource)
   resource_type = classify_resource_type(resource)

   if resource_type is None:
      # This is probably from a typo somewhere in the input
#       sys.stderr.write("Could not classify or find the input resource. \
# Check for typos and try again.\n")
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
   remote RPMs, directory indexes, and input files. They're classified
   by matching the following patterns:

   - Remote RPMS start with http[s] and end with .RPM
   - Directory indexes start with http[s] and don't end in .RPM
   - Input files don't match above, exist() on local filesystem
   """
   if is_remote_package(resource):
#       print "remotes.py[classify_resource_type()]: \
# Classified %s as a remote package" % resource
      return REMOTE_PKG_TYPE
   elif is_directory_index(resource):
#       print "remotes.py[classify_resource_type()]: \
# Classified %s as a directory index" % resource
      return REMOTE_INDEX_TYPE
   elif exists(expanduser(resource)):
#       print "remotes.py[classify_resource_type()]: \
# Classified %s as an input file" % resource
      return REMOTE_INPUT_FILE_TYPE
   else:
#       print "remotes.py[classify_resource_type()]: \
# Classified %s as unclassifiable" % resource
      return None


def is_remote_package(resource):
   """
   Classify the input resource as a remote RPM or not.
   """
   remote_regexp = re.compile(r"^https?://(.+).rpm$", re.I)
   result = remote_regexp.match(resource)

   if result is not None:
#       if options.verbosity > 1:
#          sys.stderr.write("remotes.py[is_remote_package()]: \
# %s matches remote package regexp.\n" % resource)
      return True
   else:
#       if options.verbosity > 1:
#          sys.stderr.write("remotes.py[is_remote_package()]: \
# %s doesn't match remote package regexp.\n" % resource)
      return False


def is_directory_index(resource):
   """
   Classify the input resource as a directory index or not.
   """
   remote_regexp = re.compile(r"^https?://(.+)/?$", re.I)
   result = remote_regexp.match(resource)

   if result is not None:
#       if options.verbosity > 1:
#          sys.stderr.write("remotes.py[is_directory_index()]: \
# %s matches directory index regexp.\n" % resource)
      return True
   else:
#       if options.verbosity > 1:
#          sys.stderr.write("remotes.py[is_directory_index()]: \
# %s doesn't match directory index regexp.\n" % resource)
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
#    if options.verbosity > 1:
#       sys.stderr.write("remotes.py[parse_input_file()]: \
# Input file parsed into: %s\n" % str(remotes_list))

   remote_packages = [pkg for pkg in remotes_list if is_remote_package(pkg) == True]
#    if options.verbosity > 1:
#       sys.stderr.write("remote.py[parse_input_file()]: \
# remote_packages filtered into %s\n" % str(remote_packages))

   excluded_data = [datum for datum in remotes_list if datum not in remote_packages]
#    if options.verbosity > 1:
#       sys.stderr.write("remote.py[parse_input_file()]: \
# excluded_data filtered into %s\n" % str(excluded_data))

   http_indexes = [index for index in excluded_data if is_directory_index(index)]
   remotes_from_indexes = reduce(lambda x, y: x+parse_directory_index(y), http_indexes, [])

   return (remote_packages + remotes_from_indexes, excluded_data)


def parse_directory_index(directory_index):
    """
    Retrieve a directory index and make a list of the RPMs listed.

    Returns empty list and notifies user if BeautifulSoup library is not installed.
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
    # if options.verbosity > 0:
    #    sys.stderr.write("remotes.py[parse_directory_index()]: Discovered "
    #                     + "these remote RPMs:\n")
       # for remote in remote_list:
       #    sys.stderr.write("    %s\n" % remote)

    return remote_list
