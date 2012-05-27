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


from functools import wraps
from itertools import chain, izip_longest
from tablemaker.markdown import readers

def on_each_paragraph(fn):
    @wraps(fn)
    def _wrapper(text, *args, **kwargs):
        ret = []
        for prefix, p in readers.blocks(text):
            ret.extend((prefix, fn(p, *args, **kwargs)))
        return ''.join(ret)
    return _wrapper

def table(titles, align, iterable):
    """yields a reddit table as wide as the titles iterable"""
    return generate_reddit_rows(
        chain(
            (titles, make_align_row(align)),
            format_paragraphs(
                normalize_rows(
                    len(titles),
                    iterable
                    )
                )
            )
        )


def make_align_row(align):
    return (':--' if x < 0 else '--:' if x > 0 else ':--:'
            for x in align)

def generate_reddit_rows(iterable):
    for row in iterable:
        yield '|'.join(cell.replace('|', ' ') for cell in row)

def normalize_rows(length, iterable, padding=('',)):
    for row in iterable:
        rlen = len(row)
        if rlen < length:
            yield row + padding * (length - rlen)
        else:
            yield row[:length]

def format_paragraphs(iterable):
    for row in iterable:
        for newrow in izip_longest(
                *list(readers.blocks_nosep(cell) for cell in row),
                fillvalue=' '
            ):
            yield (
                (cell.replace('\r', ' ').replace('\n', ' ') if cell else ' ')
                for cell in newrow
                )
