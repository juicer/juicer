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

import json
import juicer.utils.Log
import juicer.utils
from juicer.common.Errors import JuicerRepoExclusionError


class Repo(object):
    """
    Internal representation of a repository object

    XXX: Don't set the 'env' attribute directly! Use Repo.set_env()
    """
    def __init__(self, repo_name, env=None, repo_def=None, pulp_def=None):
        """
        `repo_name` - Name of this repo
        `env` - Environment the repo lives in
        `repo_def` - Repository definition as per juicer (see: docs/markdown/repo_syntax.md)
        `pulp_def` - Repository definition as per pulp (see: [1] for an example)

        Note: Only one of `repo_def` and `pulp_def` may be given during instantiation

        Note: Repo objects only handle updating `checksum_type` currently

        [1] https://pulp-dev-guide.readthedocs.org/en/pulp-2.3/integration/rest-api/repo/retrieval.html#retrieve-a-single-repository
        """
        juicer.utils.Log.log_debug("creating repo object for %s-%s" % (repo_name, env))
        if repo_def and pulp_def:
            raise JuicerRepoExclusionError("While instantiating repo '%s': 'repo_def' and 'pulp_def' cannot be set at the same time" % repo_name)

        self.spec = {}
        self['env'] = env

        if repo_def:
            self._parse_repo_def(repo_def)
        elif pulp_def:
            self._parse_pulp_def(pulp_def)
        else:
            self['repo_def'] = {}
            self['pulp_def'] = {}

        juicer.utils.Log.log_debug("instantiated Repo object for %s-%s" % (repo_name, env))

    def _parse_repo_def(self, repo_def):
        juicer.utils.Log.log_debug("parsing juicer definition")
        self['type'] = 'juicer'
#        self.spec = repo_def
        self['name'] = repo_def['name']
        defaults = juicer.common.Constants.REPO_DEF_DEFAULTS
        for key in juicer.common.Constants.REPO_DEF_OPT_KEYS:
            self[key] = repo_def.get(key, defaults[key])
        juicer.utils.Log.log_debug("finished parsing juicer definition")

    def _parse_pulp_def(self, repo_def):
        juicer.utils.Log.log_debug("parsing pulp definition")
        juicer.utils.Log.log_debug(juicer.utils.create_json_str(repo_def, indent=4))
        self['type'] = 'pulp'
        self.spec = repo_def
        self['name'] = repo_def['display_name']
        self['rpm_count'] = repo_def.get('content_unit_counts', {}).get('rpm', 0)
        self['srpm_count'] = repo_def.get('content_unit_counts', {}).get('srpm', 0)
        # There's no pretty way to write this that doesn't take up 10 lines of code...
        # Grab the deeply nested key 'checksum_type', or return 'sha256' if it doesn't exist
        self['checksum'] = repo_def.get('distributors', [{}])[0].get('config', {}).get('checksum_type', 'sha256')
        juicer.utils.Log.log_debug("finished parsing pulp definition")

    def set_env(self, env):
        if self['type'] == 'juicer':
            self['env'] = env
        else:
            pass

    def __setitem__(self, key, value):
        self.spec[key] = value

    def __getitem__(self, item):
        if item in self.spec:
            return self.spec[item]
        else:
            raise KeyError(item)

    def __contains__(self, item):
        return item in self.spec

    def __str__(self):
        return juicer.utils.create_json_str(self.spec)

    def _repo_ds(self):
        return self.spec

    def get(self, key, default=None):
        if key in self.spec:
            return self.spec[key]
        else:
            return default

# Custom encoder for Repo types so we can dump them with standard json tools
class RepoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Repo):
            return obj._repo_ds()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
