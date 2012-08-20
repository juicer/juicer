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

import argparse
import getpass


class PromptAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # If no value then we need to prompt for it...
        if len(values) == 0:
            values.append(getpass.getpass())

        # Save the results in the namespace using the destination
        # variable given to the constructor.
        setattr(namespace, self.dest, values)
