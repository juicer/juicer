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


class Repo(object):
    """
    Internal representation of a repository object
    """
    def __init__(self, repo_name, env=None, repo_def=None):
        """`repo_name` - Name of this repo

        `env` - Environment the repo lives in (only necessary for pulp repos)

        `repo_def`- Repository definition. Juicer or pulp style (see:
        docs/markdown/repo_syntax.md and the Pulp/JuicerRepo
        subclasses below)
        """
        juicer.utils.Log.log_debug("creating repo object for %s-%s" % (repo_name, env))
        self.spec = {}
        self['env'] = env
        self._parse_repo_def(repo_def)
        juicer.utils.Log.log_debug("instantiated Repo object for %s-%s" % (repo_name, env))

    def _parse_repo_def(self, repo_def):
        raise NotImplementedError("Don't call the Repo object directly. Instead call a PulpRepo or JuicerRepo")

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


class JuicerRepo(Repo):
    """
    Internal representation of a Juicer repository object
    """
    def _parse_repo_def(self, repo_def):
        self['name'] = repo_def['name']
        juicer.utils.Log.log_debug("parsing juicer definition for %s", self['name'])
        defaults = juicer.common.Constants.REPO_DEF_DEFAULTS
        for key in juicer.common.Constants.REPO_DEF_OPT_KEYS:
            self[key] = repo_def.get(key, defaults[key])
            juicer.utils.Log.log_debug("Defined %s as %s" % (key, str(self[key])))
        juicer.utils.Log.log_debug("finished parsing juicer definition")


class PulpRepo(Repo):
    """
    Internal representation of a Pulp repository object
    """
    def _parse_repo_def(self, repo_def):
        self.spec = repo_def
        self['name'] = repo_def['display_name']
        juicer.utils.Log.log_debug("parsing pulp definition for %s", self['name'])
        self['rpm_count'] = repo_def.get('content_unit_counts', {}).get('rpm', 0)
        self['srpm_count'] = repo_def.get('content_unit_counts', {}).get('srpm', 0)
        # There's no pretty way to write this that doesn't take up 10
        # lines of code...  Grab the deeply nested key
        # 'checksum_type', or return the default checksum_type if it
        # doesn't exist
        default_cs = juicer.common.Constants.REPO_DEF_DEFAULTS['checksum_type']
        self['checksum_type'] = repo_def.get('distributors', [{}])[0].get('config', {}).get('checksum_type', default_cs)

        # Does this thing even have an importer defined?
        self['feed'] = None
        if 'importers' in self.spec:
            # Assume we were intelligent any only defined one importer
            importer = self.spec['importers'][0]
            if 'config' in importer:
                # Good, it is configured
                if 'feed' in importer['config']:
                    # OK, it has a feed set, track it
                    self.spec['feed'] = importer['config']['feed']
        juicer.utils.Log.log_debug("finished parsing pulp definition")

    def to_juicer_repo(self):
        """Returns a JuicerRepo() object representing this pulp repo"""
        repo_def = {}
        defaults = juicer.common.Constants.REPO_DEF_DEFAULTS
        repo_def['name'] = self['name']
        for key in juicer.common.Constants.REPO_DEF_OPT_KEYS:
            repo_def[key] = self.spec.get(key, defaults[key])
            juicer.utils.Log.log_debug("Defined %s as %s" % (key, str(self[key])))
        return JuicerRepo(None, repo_def=repo_def)


class RepoDiff(object):
    """Calculate the difference of a juicer repo and a pulp repo."""
    def __init__(self, juicer_repo=None, pulp_repo=None):
        if not type(juicer_repo) == juicer.common.Repo.JuicerRepo:
            raise TypeError("juicer_repo parameter to RepoDiff is not a JuicerRepo: %s" %
                            type(juicer_repo))

        if not type(pulp_repo) == juicer.common.Repo.PulpRepo:
            raise TypeError("pulp_repo parameter to RepoDiff is not a PulpRepo %s" %
                            type(pulp_repo))

        self.j = juicer_repo
        self.p = pulp_repo
        self.distributor_diff = {}
        self.distributor_diff['distributor_config'] = {}
        self.importer_diff = {}
        self.importer_diff['importer_config'] = {}
        self._diff()

    def diff(self):
        """Return importer/distributor diff specs"""
        return {
            'distributor': self.distributor_diff,
            'importer': self.importer_diff
        }

    def __str__(self):
        return str({
            'distributor': self.distributor_diff,
            'importer': self.importer_diff
        })

    def _diff(self):
        """Calculates what you need to do to make a pulp repo match a juicer repo def"""
        j_cs = self.j['checksum_type']
        j_feed = self.j['feed']

        p_cs = self.p['checksum_type']
        p_feed = self.p['feed']

        # checksum is a distributor property
        # Is the pulp checksum wrong?
        if not p_cs == j_cs:
            juicer.utils.Log.log_debug("Pulp checksum_type does not match juicer")
            self.distributor_diff['distributor_config']['checksum_type'] = j_cs
            juicer.utils.Log.log_debug("distributor_config::checksum_type SHOULD BE %s" % j_cs)

        # feed is an importer property
        if not p_feed == j_feed:
            juicer.utils.Log.log_debug("Pulp feed does not match juicer")
            self.importer_diff['importer_config']['feed'] = j_feed
            juicer.utils.Log.log_debug("importer_config::feed SHOULD BE %s" % j_feed)


# Custom encoder for Repo types so we can dump them with standard json tools
class RepoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Repo):
            return obj._repo_ds()
        elif isinstance(obj, RepoDiff):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
