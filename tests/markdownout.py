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


#!/usr/bin/python

import unittest

from tablemaker import markdownout

class MDOutTests(unittest.TestCase):
    def setUp(self):
        self.input = (
                ('one', 'two', 'three'),
                ('alpha', 'beta'),
                ('1', '2', '3', '4'),
            )

    def test_normalize(self):
        self.assertEqual(
            list(markdownout.normalize_rows(3, self.input)),
            [('one', 'two', 'three'), ('alpha', 'beta', ''), ('1', '2', '3')])

    def test_generate(self):
        self.assertEqual(
            list(markdownout.generate_reddit_rows(
                    markdownout.normalize_rows(3, self.input)
                    )),
            ['one|two|three', 'alpha|beta|', '1|2|3']
            )

if __name__ == '__main__':
    unittest.main()
