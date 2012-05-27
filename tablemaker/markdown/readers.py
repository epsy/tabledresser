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


from itertools import izip, islice
import re

link_re = re.compile(r'(?<!\\)\[(?P<text>.*)(?<!\\)\](?<!\\)\((?P<address>.*?)(?: (?<!\\)"(?P<title>.*)(?<!\\)")?(?<!\\)\)|(?P<autolink>\b(?:http|https|ftp|ssh)://(?P<host>[0-9a-zA-Z_-]+\.[0-9a-zA-Z_.-]+)(?:/\S+)?)(?:\S|$)')

def link_sub(repl, text):
    return link_re.sub(repl, text)

blocksplit_re = re.compile(
    r'''
        (
            (?:^(?!\n)|\n+)\s*(?:[0-9]+\.\s|\*\s|(?=>))
           |(?:^(?!\n)|\n\n+|\s{2,}\n+)(?!\s*(?:[0-9]\.\ |\*\s|>))
        )''', re.X)

def blocks(text):
    sep = ''
    for block_or_sep in blocksplit_re.split(text):
        if sep is None:
            sep = block_or_sep
        else:
            if sep or block_or_sep:
                yield sep, block_or_sep
            sep = None

def blocks_nosep(text):
    for sep, block in blocks(text):
        yield block
