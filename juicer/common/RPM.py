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

import os.path
import juicer.utils
import juicer.utils.Log
import re

class RPM(object):
    def __init__(self, source):
        self.pgk_name = os.path.basename(source)
        # Source is the original location of this RPM. That includes
        # both http://.... RPMs and local /home/bro/... ones.
        self.source = source
        # If this rpm has to be synced later we'll use this to filter
        # out just those RPMs.
        self.modified = False

        url_regex = re.compile(r'^(http)s?://')

        if url_regex.match(self.source):
            self.synced = False
            self.path = None
        else:
            self.synced = True
            self.path = source

    def sync(self, destination):
        dest_file = os.path.join(destination, self.pgk_name)

        # This is the case with stuff that already exists locally
        if self.synced and self.source:
            return True

        if not os.path.exists(destination):
            os.mkdir(destination)

        self.path = dest_file
        juicer.utils.Log.log_debug("Beginning remote->local sync: %s->%s" % (self.source, self.path))
        juicer.utils.save_url_as(self.source, dest_file)
        self.modified = True
        self.synced = True
