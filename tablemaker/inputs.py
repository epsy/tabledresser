# tabledresser - a reddit bot that turns AMAs into tables
# Copyright (C) 2012-2015  Yann Kaiser
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

import httplib2
import os.path

from json import loads, load

try:
    raw_input
except NameError:
    raw_input = input # py3k renames raw_input to input

def _collect_input(row):
    return raw_input(str(len(row) + 1) + ' >')

def interactive_stdin(columns):
    text = ''
    count = 1
    while True:
        print('Row {0}:'.format(count))
        row = []
        while len(row) < columns:
            text = text.strip() + (' ' + _collect_input(row)
                                   if '|' not in text else '')
            while '|' in text and len(row) < columns:
                cell, text = text.split('|', 1)
                row.append(cell.strip())
        count += 1
        yield row

def redditlink(url, sort='best'):
    url += '?sort=' + sort
    h = httplib2.Http(".cache")
    response, content = h.request(url)
    feed = loads(content.decode('utf-8'))
    return feed

def cachedredditlink(filename):
    feed = load(open(os.path.expanduser(filename), 'r'))
    return feed
