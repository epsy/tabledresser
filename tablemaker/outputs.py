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

import sys
import os

def linesep(iterable, limit=9000, intro="", outro="", file=sys.stdout, sep='\n'):
    """Joins iterable with sep to file until limit is reached"""
    length = alength = len(intro) + len(outro)

    if intro:
        print(intro, file=file, end=sep)

    i = 0
    for line in iterable:
        length += len(line)
        if length > limit:
            length -= len(line)
            if i < 3 and len(line) > (limit - alength) * 0.7:
                continue
            else:
                break
        i += 1
        print(line.encode('utf-8') if file==sys.stdout else line,
              file=file, end=sep)

    if outro:
        print(outro, file=file, end=sep)

