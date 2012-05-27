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


def paragraphs(text):
    return text.split('\n\n')

def flatten(text):
    return text.replace('\n')

def replace_blockquotes(paragraph, before='*', after='*', flatten=True):
    if paragraph.lstrip().startswith('>'):
        return before + (' ' if flatten else '\n').join(
            line.lstrip('> ') for line in paragraph.split('\n')
            ) + after
    return paragraph

def flatten_paragraph(paragraph):
    return replace_blockquotes(paragraph)

