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

from juicer.common import Constants
from juicer.common.Errors import *
from time import sleep
import juicer.utils


class TaskPoller(object):
    def __init__(self, task_id, connectors, env, sleep_time=5):
        self.task_id = task_id
        self.connectors = connectors
        self.env = env
        self.sleep_time = sleep_time

    def poll_until_finished(self):
        juicer.utils.Log.log_debug("BEGIN POLL TASK STATE: %s" % self.task_id)
        while True:
            _r = self.connectors[self.env].get("/tasks/%s/" % self.task_id)
            if _r.status_code != Constants.PULP_GET_OK:
                _r.raise_for_status()
            else:
                state = juicer.utils.load_json_str(_r.content)['state'].strip()
                if state == 'finished':
                    juicer.utils.Log.log_debug("TASK: %s STATE: %s" % (self.task_id, state))
                    break
            sleep(self.sleep_time)
            juicer.utils.Log.log_debug("TASK: %s STATE: %s ... sleeping for %d seconds" % (self.task_id, state, self.sleep_time))
