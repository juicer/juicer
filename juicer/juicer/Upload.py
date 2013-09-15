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

import threading
import Queue
import juicer.utils

class Upload(threading.Thread):
    def __init__(self, juicer, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.juicer = juicer

    def run(self):
        while True:
            (repo, item, env) = self.queue.get()
            juicer.utils.upload_rpm(str(item.path), "%s-%s" % (repo, env), self.juicer.connector(env))
            self.queue.task_done()
