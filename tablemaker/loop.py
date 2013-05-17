# tabledresser - a reddit bot that turns AMAs into tables
# Copyright (C) 2012  Yann Kaiser
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


from __future__ import print_function

import sched
import time
import traceback
import sys
from praw.errors import RateLimitExceeded
from collections import namedtuple

RedditAction = namedtuple('RedditAction', ('fn', 'args', 'kwargs', 'attempts', 'delay'))

scheduler = sched.scheduler(time.time, time.sleep)
enter = scheduler.enter
run = scheduler.run

def noop():
    pass

class RedditSubmitter:
    """Delays multiple submissions to reddit."""

    max_attempts = 3
    default_delay = 3

    def __init__(self):
        self._queue = []
        self.stop_when_empty = True

    def enter(self, fn=noop, *args, **kwargs):
        """Enter a new submission action"""
        delay = kwargs.pop('_delay', self.default_delay)
        self._queue.append(
            RedditAction(fn, args, kwargs, self.max_attempts, delay))

    def run(self):
        if self._queue:
            fn, args, kwargs, attempts, delay = self._queue.pop(0)
            try:
                ret = fn(*args, **kwargs)
            except RateLimitExceeded as e:
                print("Repeating", fn, "later")
                self._queue.append(
                    RedditAction(fn, args, kwargs, attempts, e.sleeptime)
                    )
            except:
                print("Error while running", fn, args, kwargs, file=sys.stderr)
                traceback.print_exc()
            else:
                if ret and attempts - 1:
                    print('Will retry', fn.func_name)
                    self._queue.append(
                        RedditAction(fn, args, kwargs, attempts - 1, delay))
                elif ret:
                    print("Won't retry", fn.func_name)
            if not (self._queue or self.stop_when_empty):
                print("Waiting for more submissions to process...")
        if self._queue or not self.stop_when_empty:
            if self._queue:
                delay = self._queue[0].delay
                print("{0} submission(s) in queue".format(len(self._queue)))
            else:
                delay = self.default_delay
            scheduler.enter(delay, 0, self.run, ())

rs = RedditSubmitter()
ratelimit = rs.enter
enter(0, 0, rs.run, ())

