# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2014, Red Hat, Inc.
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


"""
Repository Definition file validation functions.

- Start by passing a document path to `validate_document`.

- Wrap in a try/except

- except for `JuicerRepoDefError`
"""


from juicer.common.Errors import *
import juicer.utils
import juicer.common.Constants
import re
import sys

valid_repo_name = re.compile('^([a-zA-Z0-9-_.]+)$')


def validate_document(document_path):
    try:
        defs = juicer.utils.read_json_document(document_path)
    except ValueError, e:
        raise JuicerRepoDefError("Could not validate: %s" % str(e))

    if is_list(defs):
        for repo_def in defs:
            validate_definitions(defs)
    else:
        raise JuicerRepoDefError("Document is not a list")

    return defs


def is_list(ds):
    return type(ds) == list


def is_dict(ds):
    return type(ds) == dict


def is_valid_checksum(cs):
    legacy = juicer.common.Constants.REPO_DEF_LEGACY_CHECKSUM_TYPES
    current = juicer.common.Constants.REPO_DEF_CHECKSUM_TYPES
    return cs in legacy or cs in current


def has_valid_keys(ds):
    keys = ds.keys()
    required_keys = juicer.common.Constants.REPO_DEF_REQ_KEYS
    optional_keys = juicer.common.Constants.REPO_DEF_OPT_KEYS
    if set(required_keys) & set(keys):
        remaining_keys = set(keys) - set(required_keys)
        if len(set(remaining_keys) - set(optional_keys)) > 0:
            raise JuicerRepoDefError("Extra keys found: %s" % (', '.join(set(remaining_keys) - set(optional_keys))))

        if 'env' in keys:
            if not is_list(ds['env']):
                raise JuicerRepoDefError("%s is not a list" % type(ds['env']))
            else:
                pass

        if 'checksum_type' in keys:
            if not is_valid_checksum(ds['checksum_type']):
                raise JuicerRepoDefError("Invalid checksum_type in repo def: %s" % ds['checksum_type'])
            else:
                pass

        if 'feed' in keys:
            if not ds['feed']:
                # Feed is undefined. Which is OK!
                pass
            elif not is_string(ds['feed']):
                raise JuicerRepoDefError("%s is not a string" % type(ds['feed']))
            else:
                pass

        return True
    else:
        raise JuicerRepoDefError("Missing required keys: %s" % ', '.join(required_keys))


def is_valid_repo_name(repo_name):
    match = valid_repo_name.match(repo_name)
    if match:
        return True
    else:
        return False


def is_string(str):
    return (type(str) == str) or (type(str) == unicode)


def validate_definitions(defs):
    for definition in defs:
        if is_dict(definition):
            validate_def_keys(definition)
        else:
            raise JuicerRepoDefError("Repo definition is not a dictionary!")


def validate_def_keys(definition):
    if has_valid_keys(definition):
        if not is_valid_repo_name(definition['name']):
            raise JuicerRepoDefError("Repo name is invalid: %s" % definition['name'])
    else:
        raise JuicerRepoDefError("Repo definition has invalid keys")

if __name__ == '__main__':
    passes = 0
    failures = 0

    for f in sys.argv[1:]:
        try:
            validate_document(f)
        except JuicerRepoDefError, e:
            failures += 1
            print "\033[00;31mFAIL:\033[0m %s: %s" % (f, str(e))
        else:
            passes += 1
            print "\033[00;32mPASS:\033[0m %s" % f

    sys.exit(failures)
