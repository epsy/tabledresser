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


import re
from tablemaker.markdown import readers

class Format(object):
    def apply(self, text, *args, **kwargs):
        return self.do_apply(self.do_remove(text), *args, **kwargs)

    def do_apply(self, text, *args, **kwargs):
        raise NotImplementedError

    def remove(self, text):
        return self.do_remove(text)

    def do_remove(self, text):
        raise NotImplementedError

    def escape(self, text):
        raise NotImplementedError

class InlineFormat(Format):
    def _iterate(self, text, fn, *args, **kwargs):
        ret = []
        for prefix, paragraph in readers.blocks(text):
            ret.extend(
                (prefix, fn(paragraph, *args, **kwargs)))
        return ''.join(ret)

    def _remove_and_apply(self, text, *args, **kwargs):
        return self.do_apply(self.do_remove(text), *args, **kwargs)

    def apply(self, text, *args, **kwargs):
        return self._iterate(text, self._remove_and_apply, *args, **kwargs)

    def remove(self, text):
        return self._iterate(text, self.do_remove)


class ReFormat(Format):
    def do_remove(self, text):
        return self.format_re.sub(r'\g<text>', text)

    def escape(self, text):
        return self.escape_open(self.escape_close(text))

    def escape_open(self, text):
        return self.open_re.sub(r'\\\g<0>', text)

    def escape_close(self, text):
        return self.close_re.sub(r'\\\g<0>', text)

trim_re = re.compile(r'^(?P<pre>\s*)(?P<text>.+?)(?P<suf>\s*)$')

class WrapFormat(InlineFormat, ReFormat):
    def __init__(self, prefix, suffix=None):
        self.prefix = prefix
        self.suffix = suffix or prefix
        self.format_re, self.open_re, self.close_re = self._make_re()

    def _make_re(self):
        prefix = re.escape(self.prefix)
        suffix = re.escape(self.suffix)
        return re.compile(
                ur'(?<!\\){0}(?P<text>.+?)(?<!\\){1}'.format(
                    prefix, suffix)
            ), re.compile(
                ur'(?<!\\){0}(?!\s)'.format(prefix)
            ), re.compile(
                ur'(?<!\\|\s){0}'.format(suffix)
            )

    def do_apply(self, text):
        pre, text_, suf = trim_re.match(text).groups()
        return (
            pre + self.prefix
            + self.escape_close(text_)
            + self.suffix + suf
            )

    def __unicode__(self):
        return u'WrapFormat: {0}text{1}'.format(self.prefix, self.suffix)

    def __repr__(self):
        return u'<{0}>'.format(self)

class EmFormat(WrapFormat):
    def _make_re(self):
        prefix = re.escape(self.prefix)
        suffix = re.escape(self.suffix)
        return re.compile(
                ur'(?<!\\|{0}){0}(?!\\|\s|{0})(?P<text>.+?)(?<!\\|\s|{1}){1}(?!{1})'.format(
                    prefix, suffix)
            ), re.compile(
                ur'(?<!\\|{0}){0}(?!\s|{0})'.format(prefix)
            ), re.compile(
                ur'(?<!\\|\s|{0}){0}(?!{0})'.format(suffix)
            )

em = EmFormat('*')
strong = WrapFormat('**')
strike = WrapFormat('~~')

class LinkFormat(InlineFormat, ReFormat):
    format_re = re.compile(r'(?<!\\)\[(?P<text>.*?)(?<!\\)\](?<!\\)\((?P<address>.*?)(?: (?<!\\)"(?P<title>.*?)(?<!\\)")?(?<!\\)\)|(?P<autolink>\b(?:http|https|ftp|ssh)://(?P<host>[0-9a-zA-Z_-]+\.[0-9a-zA-Z_.-]+)(?:/\S+)?)(?:\S|$)')
    open_re = re.compile(r'\[')
    close_re = re.compile(r'[)\]]')

    def do_apply(self, text, address, title=''):
        return u'[{0}]({1}{2})'.format(
            self.escape(text), address,
            u' "' + title + u'"' if title else ''
            )

    def _text_sub(self, match):
        if match.group('autolink'):
            return match.expand(r'Link to \g<host>')
        else:
            return match.group('text')

    def do_remove(self, text):
        return self.format_re.sub(self._text_sub, text)

    def _shorten_link(self, match, autolink_fmt='Link to {host}'):
        if match.group('autolink'):
            return self.apply(
                autolink_fmt.format(host=match.group('host')),
                match.group('autolink')
                )
        else:
            return self.apply(*match.groups()[:-2])

    def _shorten(self, text, **kwargs):
        return self.format_re.sub(self._shorten_link, text, **kwargs)

    def shorten(self, text, **kwargs):
        return self._iterate(text, self._shorten, **kwargs)

    def iterate(self, text):
        return self.format_re.finditer(text)

link = LinkFormat()

