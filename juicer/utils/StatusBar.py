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

import os
import sys


class StatusBar(object):
    def __init__(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        self.width = int(columns) - 2
        sys.stdout.write("[%s]" % (" " * self.width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.width + 1))
    
    def update(self, chunksize, totalsize):
        if chunksize > totalsize:
            sys.stdout.write("=" * self.columns)
            sys.stdout.flush()
        else:
            sys.stdout.write("=" * int((float(chunksize)*self.width) / float(totalsize)))
            sys.stdout.flush()
        
    def close(self):
        sys.stdout.write("\n")
