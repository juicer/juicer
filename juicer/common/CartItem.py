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

from juicer.common.RPM import RPM
import juicer.utils.Log
import juicer.common.RPM
import juicer.utils.Log
import juicer.utils
import os
import os.path


class CartItem(object):
    def __init__(self, path=None):
        """
        Represents an RPM item in a Cart object.

        Originated from issue:90. *Intends* to simplify operations
        like checking is_signed, accesing the items simple
        name/version/release, and to implement the juicer create-like
        and update functionality.

        The optional `path` parameter can be used to fill in all
        attributes when the object is instantiated.
        """
        self._reset()
        if path:
            self.update(path)

    def update(self, path):
        """
        Update the attributes of this CartItem.
        """
        self._reset()
        self.path = path
        self._refresh_synced()
        if self.is_synced:
            self._refresh_path()
            self._refresh_signed()
            self._refresh_nvr()

    def refresh(self):
        """
        Call when something outside of a CartItem modifies the items's
        contents, for example: an external RPM Signing utility.
        """
        self.update(self.path)

    def sync_to(self, destination):
        """
        Sync an RPM from a REMOTE to a LOCAL path.

        Returns True if the item required a sync, False if it already
        existed locally.

        TODO: Remove dupe code in Cart.py:sync_remotes()
        """
        rpm = RPM(self.path)
        rpm.sync(destination)
        if rpm.modified:
            juicer.utils.Log.log_debug("Source RPM modified. New 'path': %s" % rpm)
            self.update(rpm.path)
            return True
        return False

    def _refresh_synced(self):
        """
        Update our is_synced attribute accordingly.
        """
        if self.path.startswith('http'):
            juicer.utils.Log.log_debug("%s is not synced" % self.path)
            self.is_synced = False
        else:
            juicer.utils.Log.log_debug("%s is synced" % self.path)
            self.is_synced = True

    def _refresh_path(self):
        """ Does it exist? Can we read it? Is it an RPM? """
        # Unsynced items are remote so we can't check some of their
        # properties yet
        if os.path.exists(self.path):
            try:
                i = open(self.path, 'r')
                i.close()
                juicer.utils.Log.log_debug("Successfully read item at: %s" % self.path)
            except:
                raise IOError("Error while attempting to access item at path: %s" % self.path)
        else:
            raise IOError("Could not locate item at path: %s" % self.path)

    def _refresh_nvr(self):
        """ Refresh our name-version-release attributes. """
        rpm_info = juicer.utils.rpm_info(self.path)
        self.name = rpm_info['name']
        self.version = rpm_info['version']
        self.release = rpm_info['release']

    def _refresh_signed(self):
        """
        Check if the item is signed with a key and update our
        is_signed attribute accordingly.
        """
        self.is_signed = juicer.utils.check_sig(self.path)

    def _reset(self):
        """ Used during update operations and when initialized. """
        self.path = ''
        self.version = ''
        self.release = ''
        self.is_signed = False
        self.is_synced = False
        self.rpm = False

    def __str__(self):
        return str(self.path)
