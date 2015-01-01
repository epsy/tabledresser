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

from tablemaker.redditfilters import (
    joinlines, removelinks, keep_only_questions,
    )

class DummyQuestion(unittest.TestCase):
    question = """\
Dont customers realise if their cars need new pads ?"""
    answer = """\
You'd be surprised at what people don't know. I guess it'd be like someone trying to describe HTML coding to me. Yeah, I understand what it does, but not how it works."""

    question_join = question
    answer_join = answer

    def test_join(self):
        self.assertEqual(
            joinlines(self.answer),
            self.answer_join)
        self.assertEqual(
            joinlines(self.question),
            self.question_join)

    question_nolinks = question
    def test_nolinks(self):
        self.assertEqual(
            removelinks(self.question),
            self.question_nolinks
            )

    question_question = question
    def test_question(self):
        self.assertEqual(
            keep_only_questions(self.question),
            self.question_question
            )

class DummyLongQuestion(DummyQuestion):
    question = """\
Dont customers realise if their cars need new pads ? Worn pads would have several indications - squeaks, decreased braking power, shuddering (if absolutely worn) etc."""
    answer = """\
You'd be surprised at what people don't know. I guess it'd be like someone trying to describe HTML coding to me. Yeah, I understand what it does, but not how it works."""


if __name__ == '__main__':
    unittest.main()
