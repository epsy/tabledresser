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

from itertools import chain, izip, izip_longest
import re
from functools import partial
from math import log
from copy import copy
from HTMLParser import HTMLParser
from collections import OrderedDict, namedtuple
from time import time

from tablemaker_orm.models import TrackedTable, SpecialRequest, REQUEST_TYPE_DELETE
from tablemaker.markdownout import flatten_paragraph
from tablemaker.markdown import readers, writers, formats

def fake_comment(text, permalink='http://test.link/'):
    return type('FakeComment', (object,), {
            'body': text,
            'permalink': permalink,
        })

def _read_replies(
        parent,
        child,
        filter_fn,
        pre_filter_fn=lambda *args: True):
    if parent and not pre_filter_fn(parent):
        return []

    ret = []
    f = filter_fn(parent, child)
    if f:
        ret.append(f)

    if hasattr(child, 'replies') and child.replies:
        for reply in child.replies:
            ret.extend(
                _read_replies(child, reply, filter_fn, pre_filter_fn)
                )

    return ret

def QandA_grab(submission, answers_from_usernames=None):
    if not answers_from_usernames:
        if not hasattr(submission.author, 'name'):
            return []
        answers_from_usernames = (
            submission.author.name,
            )

    def _filter(parent, message):
        if (    parent and hasattr(message, 'replies') and
                hasattr(parent.author, 'name') and
                hasattr(message.author, 'name') and
                message.author.name in answers_from_usernames):
            parent.body = unescape_entities(parent.body)
            message.body = unescape_entities(message.body)
            return parent, message

    return chain.from_iterable(
        _read_replies(None, comment, _filter)
        for comment in submission.comments
            )

def QandA_merge(iterable):
    qa = OrderedDict()
    for parent, message in iterable:
        if parent.content_id not in qa:
            qa[parent.content_id] = (parent, [message])
        else:
            for message_ in qa[parent.content_id][1]:
                if message_.body == message.body:
                    break
            else:
                qa[parent.content_id][1].append(message)
    for parent, messages in qa.values():
        messages.sort(key=lambda x: x.created_utc)
        messages[0].body = '\n\n'.join(message.body for message in messages)
        yield parent, (messages[0])


def QandA_sort_votecount(iterable):
    answers = {}
    def key_fn(x):
        parent, message = x
        if parent.parent_id in answers and answers[parent.parent_id]:
            score = answers[parent.parent_id] - 1
        else:
            score = (
                ((parent.ups - parent.downs) * 5 + message.ups + message.downs)
                * log(len(message.body)) * message.ups
                * log(2 ** parent.body.count('?'))
                )
        answers[message.content_id] = score
        return score
    return sorted(iterable, key=key_fn, reverse=True)

def is_blockquote_attempt(phrase, rphrase):
    return (
        phrase.startswith('>')
        or rphrase.startswith('    ')
        or phrase.startswith('*') and phrase.endswith('*')
        or phrase.startswith('"') and phrase.endswith('"')
        )

blocksplit_re = re.compile(r'(?:^|\n+)\s*(?:[0-9]+\. |\* |(?=>))|(?:\n\n+| {2,}\n+)(?!\s*(?:[0-9]\.|[*>]))')
sentence_re = re.compile(r'(?<=[?!.])\s+(?=[0-9A-Z])')
wordsplit_re = re.compile('[/ \t\n\r\f\v.?;,!()[\]]+')
quote_re = re.compile('^\s+&gt;')
def QandA_splitquestions(iterable):
    for question, answer in iterable:
        q = list(
            flatten_paragraph(reformat(
                formats.link.remove(p)
                ))
            for p in
            remove_thank_blocks(readers.blocks_nosep(question.body))
            )
        a = list(remove_thank_blocks(readers.blocks_nosep(
            formats.link.shorten(answer.body)
            )))

        # first, try to match blockquotes against questions
        # and treat fully strong/emphasised paragraphs as such(courtesy of mojangles)
        quote = False
        last_quote = False
        q_ = []
        a_ = []
        for phrase, rphrase in ((phrase_.strip(), phrase_) for phrase_ in a):
            if is_blockquote_attempt(phrase, rphrase):
                phrase = phrase.lstrip('*> "').rstrip(' *"')
                if phrase in q or phrase in question.body:
                    if last_quote:
                        q_[-1].append(phrase)
                    else:
                        q_.append([phrase])
                    last_quote = quote = True
            elif quote:
                if last_quote:
                    a_.append([phrase])
                else:
                    a_[-1].append(phrase)
                last_quote = False
        if quote:
            if not (q_ and a_):
                continue
            try:
                q, a = [list(chain(*l)) for l in zip(
                        *[
                            (['  '.join(ques)] + [''] * (len(ans) - 1), ans)
                            for ques, ans in izip(q_, a_)
                            ]
                        )
                    ]
            except ValueError:
                print(q_, a_)
                raise
            diff = 0
        else:
            diff = len(q) - len(a)

        if len(q) == 1 or len(a) == 1:
            q = ['  '.join(q)]
            diff = 0

        if diff < 0:
            q_ = list(chain.from_iterable(questions(q__) for q__ in q))
            if not q_:
                a = [' '.join(a)]
                diff = 0
            else:
                diff_ = len(q_) - len(a)
                if not diff_:
                    q = q_
                    diff = 0

        if diff:
            words_q = list(words(phrase) for phrase in q)
            words_a = list(words(phrase) for phrase in a)

            scores = {}
            total = 0
            amount = 1
            for i, wordset in enumerate(words_q):
                for j, wordset_ in enumerate(words_a):
                    inter = wordset & wordset_
                    score = len(inter)
                    scores[(i,j)] = score
                    if score:
                        total += score
                        amount += 1

            avg = total / float(amount)

            q_ = []
            a_ = []
            positions = {}
            answer_positions = {}
            used_q = []
            used_a = []
            for (i, j), score in sorted(scores.items()):
                if score > avg:
                    pos = positions.get(i, None)
                    pos = answer_positions.get(j, pos)
                    if pos == None:
                        positions[i] = pos = len(q_)
                        q_.append([])
                        a_.append([])
                    if i not in used_q:
                        q_[pos].append(q[i])
                        used_q.append(i)
                    if j not in used_a:
                        a_[pos].append(a[j])
                        used_a.append(j)
                        answer_positions[j] = pos

            q = ('  '.join(phrase) for phrase in q_)
            a = ('  '.join(phrase) for phrase in a_)
            diff = 0

        q = filter(None, q)
        a = filter(None, a)
        if not (q and a):
            continue

        for q_, a_ in izip_longest(q, a, fillvalue=''):
            question_ = copy(question)
            question_.body = q_
            answer_ = copy(answer)
            answer_.body = reformat(a_)
            yield question_, answer_

location_p = re.compile(r'\W(?:here|there)\W')
location_re = re.compile(r'(?:in|at|by|from) (?:(?:his|her|their|my|your|our)[a-zA-Z0-9 ]+(?=,)|([A-Z][a-z]+(?:(?:[ -][A-Z]|-)[a-z]+)*)(?:, ([A-Z]+))?)', re.I)
def location_rep(i, sentences, match):
    word = match.group(0)
    if location_re.search(sentences[i]):
        return word
    else:
        for j in range(i-1, -1, -1):
            m = location_re.search(sentences[j])
            if m:
                ref = m.group(0)
                state = m.group(2)
                if state and not state.isupper():
                    ref = ref[:-len(state)-2]
                return '{word}[{ref}]'.format(word=word, ref=ref)
        else:
            return word

pronoun_re = re.compile(r'\W(?:it)\W|\W(?:this|that)\s*[.,;/!?]')

def questions(body):
    sentences = sentence_re.split(body)
    kept = []
    for i, sentence in enumerate(sentences):
        if sentence.endswith('?'):
            sentence = location_p.sub(
                            partial(location_rep, i, sentences),
                            sentence)
            pronoun = pronoun_re.search(sentence)
            if pronoun and i - 1 not in kept:
                kept.append(i - 1)
                sentence = '  '.join(sentences[i-1:i+1])

            kept.append(i)
            yield sentence

def keep_only_questions(body):
    return '  '.join(questions(body))

def is_thank_block(block):
    if not block:
        return True
    if block[-1] == ':':
        return True
    if len(block) > 30:
        return False
    txt = block.lower()
    for word in (
            'thank', 'love', 'welcome', 'hi', 'hello'
            'question', 'good',
            ):
        if word in txt:
            return True
    return False

def remove_thank_blocks(blocks):
    for block in blocks:
        if block and not is_thank_block(block):
            yield block

def unescape_entities(text):
    return HTMLParser.unescape.__func__(HTMLParser, text)

repeat_re = re.compile("(?P<char>.)(?P=char){3,}")
def reformat(body_):
    body = body_.lstrip(' .,-;/!?')
    if not body:
        return body #must be a smiley or whatever
    if body[-1].isalnum():
        body += '.'
    if body[0].islower():
        body = body[0].upper() + body[1:]
    return repeat_re.sub('\g<char>\g<char>\g<char>', body)

def remove_bad_prefixes(body):
    lower = body.lower()
    first = wordsplit_re.split(lower, 1)[0]
    if (
            first in ('or', 'and', 'edit')
            or first.startswith('first')
            or first.startswith('second')
            or first.startswith('third')
        ):
        body = body[len(first):]
    return body

def shorten_question(body):
    length = len(body)
    last = body.rfind('?', int(-7 * log(length + 1)))
    if last < 0 and length > 300:
        return None #Not a question
    body = remove_bad_prefixes(body)
    return body


_word_replaces = {
        'could': 'would',
    }
for word in """the ha do did i are them thi that or and it get wa""".split():
    _word_replaces[word] = None
def word_replaces(word):
    if len(word) < 3:
        return None
    if word[-2:] == 've':
        word = word[:-2]
    elif word[-1:] == 's':
        word = word[:-1]
    if word[-2:] == 'nt':
        word = word[:-2]
    return _word_replaces.get(word, word)

def words(phrase):
    return set(
            x for x in (word_replaces(unicode(word).translate({'"': None, "'": None}).lower())
            for word in wordsplit_re.split(phrase)) if x
        )


def tallies(message, format='^``{stars}``'):
    return ''
    score = message.ups - message.downs
    return format.format(
        stars=('+' * int(log(score)) if score > 0 else
               '-' * int(log(-score)) if score < 0 else
               '')
        )

def QandA_formatter(iterable):
    question_dismissed = False
    for question_, answer_ in iterable:
        if not question_.body and question_dismissed:
            continue
        question_dismissed = False

        question = shorten_question(
            flatten_paragraph(
                formats.link.remove(
                    question_.body)))

        if question is None:
            question_dismissed = True
            continue

        if not question and question_.body:
            continue

        yield (
            formats.link.apply(question, question_.permalink + '?context=5')
                + tallies(question_),
            formats.link.shorten(answer_.body) + tallies(answer_)
            )

def links_from_body(iterable):
    for message in iterable:
        for match in formats.link.iterate(message.body):
            yield match.groups(), message

def remove_tracked(submissions):
    for submission in submissions:
        if not TrackedTable.objects.filter(parent=submission.id).exists():
            yield submission

def iama_filter(submissions, age=12*60*60, comments=200):
    now = time()
    for submission in submissions:
        if not hasattr(submission.author, 'name'): #author probably deleted the post
            continue
        if submission.num_comments < comments or now - age < submission.created_utc:
            continue
        if SpecialRequest.objects.filter(
            parent=submission.id, type=REQUEST_TYPE_DELETE).exists():
            continue
        lower = unicode(submission.title.lower()).translate({
            ',': None,
            ':': None,
            ' ': None,
            })
        if ('request' in lower
            and 'asrequested' not in lower
            and 'byrequest' not in lower
            and 'perrequest' not in lower
            ):
            continue
        yield submission

def verify_ama(submission):
    sr = submission.subreddit
    mods = [redditor.name for redditor in sr.get_moderators()]

    for comment in submission.comments:
        if (
                hasattr(comment, 'author')
                and hasattr(comment.author, 'name')
                and comment.author.name in mods
                ):
            print(comment, comment.body)
            pass # read the post
    return False
