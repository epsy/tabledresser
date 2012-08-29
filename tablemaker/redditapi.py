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

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import httplib2
from json import load, loads
from time import sleep
import os.path
import sys
import traceback
import subprocess
import re
import json

from reddit import Reddit, errors as rerrors

from tablemaker.loop import ratelimit

# cookie = None
# modhash = None
# http = None
reddit = None

# login_url = 'https://ssl.reddit.com/api/login/{user}'
# comment_url = 'http://www.reddit.com/api/comment'
submit_url = 'http://www.reddit.com/api/submit'
edit_url = 'http://www.reddit.com/api/editusertext'
# getpm_url = 'http://www.reddit.com/message/messages.json'

reddit_re = re.compile(r'^(?:http://(?:www.)?reddit\.com)?'
                       r'(?:/r/(?P<subreddit>[^/]+))?'
                       r'/comments/(?P<id>[^/]+)'
                       r'(?:/(?P<preview>[^/]+)'
                       r'(?:/(?P<comment>[^/?]+))?)?', re.I)

def get_reddit():
    global reddit
    if not reddit:
        reddit = Reddit(user_agent='python2/reddit_api/tabledresser')
    return reddit

def login():
    r = get_reddit()
    if not r.user:
        r.login(**get_login_info())
        if not r.user:
            print("Uh! I'm still not logged in!")

def get_login_info():
    return load(open(os.path.expanduser('~/.reddit'), 'r'))

# def get_handle():
#     global http
#     if not http:
#         http = httplib2.Http()
#     return http
# 
# def set_cookie(headers, data=None):
#     global cookie, modhash
#     if not cookie:
#         h = get_handle()
#         login_info = get_login_info()
#         response, content = http.request(
#             login_url.format(user=login_info['user']),
#             'POST',
#             headers={
#                     'Content-type': 'application/x-www-form-urlencoded',
#                 },
#             body=urlencode(login_info)
#             )
#         try:
#             f = loads(content.decode('utf-8'))
#             if f['json']['errors']:
#                 sys.exit("Could not login to reddit: {msg}".format(
#                     f['json']['errors'],
#                     ))
#         except Exception as e:
#             print("Reddit did not return a json feed", file=sys.stderr)
#             traceback.print_exc()
#             sys.exit(1)
#         cookie = f['json']['data']['cookie']
#         modhash = f['json']['data']['modhash']
#         print("Logged in!")
#         ratelimit(_delay=2)
#     headers['Cookie'] = 'reddit_session=' + cookie
#     if data is not None:
#         data['uh'] = modhash
# 
# def comment(parent, text):
#     headers = {'Content-type': 'application/x-www-form-urlencoded'}
#     body = {'text': text.encode('utf-8')}
#     if parent.startswith('t3_'):
#         body['thing_id'] = parent
#     else:
#         body['parent'] = parent
#     set_cookie(headers, body)
#     h = get_handle()
#     response, content = h.request(comment_url, 'POST',
#                                   headers=headers, body=urlencode(body))
#     try:
#         f = loads(content.decode('utf-8'))
#         data = f['jquery'][18][3][0][0]['data']
#     except:
#         print(content, file=sys.stderr)
#         traceback.print_exc()
#         return ''
#     return data
# 
def submit(title, text, subreddit, captsol=None, is_link=False):
    r = get_reddit()
    body = {
        'title': title,
        'sr': subreddit,
        'r': subreddit,
        'kind': 'link' if is_link else 'self',
        'uh': r.modhash,
        'api_type': 'json',
        }
    if is_link:
        body['link'] = text
    else:
        body['text'] = text
    if captsol:
        body['iden'], body['captcha'] = captsol
    content = r._request(submit_url, body)
    try:
        f = loads(content.decode('utf-8'))
    except:
        print(content, file=sys.stderr)
        traceback.print_exc()
        return ''
    else:
        print(repr(f))
        # if f['jquery'][9][3] == 'captcha' and not f['jquery'][11][3] == 'redirect':
        #     captcha = f['jquery'][10][3][0]
        #     subprocess.call(('xdg-open', 'http://www.reddit.com/captcha/{captcha}.png'.format(captcha=captcha)))
        #     solution = raw_input('Captcha solution: ')
        #     return submit(title, text, subreddit, (captcha, solution), is_link)
        return f['json']['data']['id']

        #if not link.startswith('http://'):
        #    # Assuming we're rate-limited.
        #    if is_link:
        #        limit = f['jquery'][18][3][0]
        #    else:
        #        limit = f['jquery'][12][3][0]
        #    raise rerrors.RateLimitExceeded('RATELIMIT', limit)
        #return reddit_re.match(link).group('id')

def edit(thing_id, text, subreddit=None):
    login()
    r = get_reddit()
    body = {
            'thing_id': thing_id,
            'text': text,
            'uh': r.modhash,
            'api_type': 'json',
        }
    if subreddit:
        body['r'] = subreddit
    response = r._request(edit_url, body)
    try:
        f = json.loads(response.decode('utf-8'))
        if f['json']['errors']:
            return True
        else:
            return False
    except:
        traceback.print_exc()
    print('Got edit response:', response)
    return True

# def get_pms():
#     headers = {}
#     set_cookie(headers)
#     h = get_handle()
#     response, content = h.request(getpm_url, 'GET', headers=headers)
# 
#     try:
#         f = json.loads(content.decode('utf-8'))
#     except:
#         print("Reddit did not return a json feed", file=sys.stderr)
#         print(content)
#         return True
# 
#     return f['data']['children']
