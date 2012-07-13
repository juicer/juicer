# -*- coding: utf-8 -*-
# Taboot - Client utility for performing deployments with Func.
# Copyright © 2011-2012, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import inspect
import juicer.utils
import os.path

LOG_DEBUG = 4
LOG_NOTICE = 3
LOG_WARN = 2
LOG_INFO = 1
LOG_ERROR = 0
LOG_LEVEL_CURRENT = 1
            # error, info -> stdout
LOG_TO_STDOUT = [LOG_ERROR, LOG_INFO, LOG_NOTICE]
LOG_TO_STDERR = [LOG_DEBUG, LOG_WARN]

"""
Log levels adapted from the `Apache Commons` Logging User Guide:

http://commons.apache.org/logging/guide.html#Message%20Priorities/Levels

Each level includes all of the levels below it.

* ``Debug`` - Detailed information on the flow through the system.

* ``Warn`` - Use of deprecated APIs, poor use of API, 'almost' errors,
  other runtime situations that are undesirable or unexpected, but not
  necessarily "wrong".

* ``Info`` - Interesting runtime events (startup/shutdown). Expect
  these to be immediately visible on a console, so be conservative and
  keep to a minimum.

* ``Error`` - Severe errors that cause premature termination. This
  would rarely be seen.

For consistency, please follow this log-message style-guide:
 - Use full sentences, and end them with FULL STOPS.
 - Use ellipses when "Doing xyz..."
 - Start messages with a leading capital!

Examples:

some_thing = "something"
something = "something"
thing = "thing"

log_debug("Something is broken!!!")

log_debug("%s is broken!!!!", some_thing)

log_debug("In %s there is a broken %s.", something, thing)

log_debug("In %s there is a broken %s.", (something, thing))

log_debug("In %s there is a broken %s.", [something, thing])

"""


def log_wrap(origfunc):
    """
    DRY: Use magic instead of code to get a string for the correct log
    level when calling ``print_log_msg``. Because writing the same
    boilerplate code in each log_XXX def was too painful to commit.
    """
    def orig_func_wraper(msg, *args):
        # Take the callers name and snap it in two, result is log
        # level, e.g.: log_debug is DEBUG level.
        log_level = origfunc.__name__.split("_")[1]

        import Log
        if getattr(Log, "LOG_%s" % log_level.upper()) <= \
                Log.LOG_LEVEL_CURRENT:
            # flatten and stringify the positional params so we don't
            # tuple() a tuple or an array and end up with
            # weirdness.
            a = map(str, juicer.utils.flatten(args))
            print_log_msg(log_level, str(msg) % tuple(a))
    return orig_func_wraper


def print_log_msg(log_level, msg):
    import Log
    ll = getattr(Log, "LOG_%s" % log_level.upper())
    file_called_from = inspect.stack()[2][1]
    line_called_from = inspect.stack()[2][2]
    method_called_from = inspect.stack()[2][3]
    debug_info = "%s:%s:%s" % (os.path.basename(file_called_from),
                                 method_called_from, line_called_from)

    try:
        for l in msg.split("\n"):
            if ll in Log.LOG_TO_STDOUT:
                if log_level == "info":
                    print l
                else:
                    print "%s: %s" % (log_level, l)
            else:
                juicer.utils.print_stderr("%s[%s]: %s\n" %\
                        (log_level, debug_info, l))
    except Exception as e:
        # A logging mechanism should never cause a script to abort if
        # you can't expand all formatting markers
        juicer.utils.print_stderr("Error while processing %s message:\n%s\n" %
                          (log_level.upper(), e))


@log_wrap
def log_error(mgs, LOG_ERROR, *args):
    pass


@log_wrap
def log_warn(msg, LOG_WARN, *args):
    pass


@log_wrap
def log_info(msg, LOG_INFO, *args):
    pass


@log_wrap
def log_notice(msg, LOG_NOTICE, *args):
    pass


@log_wrap
def log_debug(msg, *args):
    pass


def _log_test():
    some_thing = "something"
    something = "something"
    thing = "thing"

    log_debug("Something is broken!!!")
    log_debug("%s is broken!!!!", some_thing)
    log_debug("In %s there is a broken %s.", something, thing)
    log_debug("In %s there is a broken %s.", (something, thing))
    log_debug("In %s there is a broken %s.", [something, thing])


if __name__ == "__main__":
    _log_test()
