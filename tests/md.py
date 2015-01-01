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


#!/usr/bin/python

import unittest
from tablemaker.markdown import readers, writers, filters, formats

class ReaderTests(unittest.TestCase):

    longtext = """\
* Block one

Block two

1. block three
2. block four
* block five

* block six

block seven  
block eight

    block nine

> block ten

block eleven"""

    def test_blocks(self):
        self.assertEquals(list(readers.blocks(self.longtext)),
            [('* ', 'Block one'),
             ('\n\n', 'Block two'),
             ('\n\n1. ', 'block three'),
             ('\n2. ', 'block four'),
             ('\n* ', 'block five'),
             ('\n\n* ', 'block six'),
             ('\n\n', 'block seven'),
             ('  \n', 'block eight'),
             ('\n\n', '    block nine'),
             ('\n\n', '> block ten'),
             ('\n\n', 'block eleven')])

class WriterTests(unittest.TestCase):

    def test_paragraph_formats(self):
        text = """\
First paragraph

Second paragraph"""

        self.assertEquals(
            writers.em(text),
            """*First paragraph*\n\n*Second paragraph*"""
            )

class FilterTests(unittest.TestCase):

    link_text = """\

http://www.google.com/search?q=Hello+World

[Follow this great link!](http://www.reddit.com/)

"""

    def test_shortenlinks(self):
        raise NotImplementedError

    def test_unlink(self):
        raise NotImplementedError

class FormatTests(unittest.TestCase):
    def test_em(self):
        self.assertEquals(formats.em.apply('hello'), '*hello*')

    def test_un_em(self):
        self.assertEquals(
            formats.em.remove('hello *world*'),
            'hello world')

    def test_em_existing(self):
        self.assertEquals(formats.em.apply('hello *world*'), '*hello world*')

    def test_em_strip(self):
        self.assertEquals(formats.em.apply(' hello '), ' *hello* ')

    def test_em_escape(self):
        self.assertEquals(formats.em.apply('hello *world'), '*hello *world*')
        self.assertEquals(formats.em.apply('hello* world'), '*hello\\* world*')
        self.assertEquals(formats.em.apply('hello\\* world'), '*hello\\* world*')

    def test_strong(self):
        self.assertEquals(formats.strong.apply('hello'), '**hello**')

    def test_strong_em(self):
        self.assertEquals(
            formats.strong.apply(formats.em.apply('hello')), '***hello***')
        self.assertEquals(
            formats.em.apply(formats.strong.apply('hello')), '***hello***')

    def test_link(self):
        self.assertEquals(
            formats.link.apply('hello', 'http://www.reddit.com/'),
            '[hello](http://www.reddit.com/)')
        self.assertEquals(
            formats.link.apply(
                'hello world', 'http://www.reddit.com/',
                'title'
                ),
            '[hello world](http://www.reddit.com/ "title")')

    def test_unlink(self):
        self.assertEquals(
            formats.link.remove('[hello](http://www.reddit.com/)'),
            'hello')
        self.assertEquals(
            formats.link.remove(
                'http://www.google.com/search?q=Hello+World'),
            'Link to www.google.com')

    def test_link_existing(self):
        self.assertEquals(
            formats.link.apply(
                'Hello [world](http://www.reddit.com/)!',
                'http://www.google.com/'),
            '[Hello world!](http://www.google.com/)'
            )

    def test_link_escape(self):
        self.assertEquals(
            formats.link.apply(
                'Hello []=]',
                'http://www.reddit.com/'),
            '[Hello \[\]=\]](http://www.reddit.com/)'
            )

if __name__ == '__main__':
    unittest.main()

