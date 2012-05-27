from __future__ import print_function
import os

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db import models
from datetime import datetime, timedelta
from json import loads, dumps

class TableManager(models.Manager):
    def xly(self, oldest, newest, period):
        now = datetime.utcnow()
        return self.filter(
            started__gte=now - timedelta(**oldest),
            started__lt=now - timedelta(**newest),
            edited__lte=now - timedelta(**period),
            )
    def hourly(self):
        return self.xly(
                {'days': 1},
                {},
                {'hours': 1}
            )

    def sixhourly(self):
        return self.xly(
                {'days': 4},
                {'days': 1},
                {'hours': 6}
            )

class TrackedTable(models.Model):
    objects = TableManager()

    comment = models.CharField(max_length=6)
    parent = models.CharField(max_length=6)
    submission = models.CharField(max_length=6)
    started = models.DateTimeField()
    edited = models.DateTimeField()

    def __unicode__(self):
        return self.parent

    def get_next_update(self):
        nexthourly = self.edited + timedelta(hours=1)
        nextsixhourly = self.edited + timedelta(hours=6)

        if nexthourly < self.started + timedelta(days=1):
            return nexthourly
        elif nextsixhourly < self.started + timedelta(days=4):
            return nextsixhourly
        return None # never

    def get_comment_url(self, subreddit=None):
        if self.comment:
            return (
                'http://www.reddit.com{reddit}/comments/{submission}/'
                'tabledresser/{comment}'.format(
                    submission=self.parent,
                    comment=self.comment,
                    reddit='/r/' + subreddit if subreddit else '',
                    )
                )

    def get_submission_url(self, subreddit=None):
        if self.submission:
            return (
                'http://www.reddit.com{reddit}/comments/{submission}/'
                .format(
                    submission=self.submission,
                    reddit='/r/' + subreddit if subreddit else '',
                ))

    def get_parent_url(self, subreddit=None):
        return (
            'http://www.reddit.com{reddit}/comments/{submission}/'
            .format(
                submission=self.parent,
                reddit='/r/' + subreddit if subreddit else '',
            ))

REQUEST_TYPE_DELETE = 0
REQUEST_TYPE_AUTHORS = 1
REQUEST_TYPES = (
    (REQUEST_TYPE_DELETE, 'Delete'),
    (REQUEST_TYPE_AUTHORS, 'Author list'),
    )
REQUEST_TYPES_DICT = dict(REQUEST_TYPES)

class SpecialRequest(models.Model):
    parent = models.CharField(max_length=6)
    type = models.SmallIntegerField(choices=REQUEST_TYPES)
    data = models.TextField(blank=True)

    def __unicode__(self):
        return u'{0} for {1}'.format(self.get_canonical_type(), self.parent)

    def get_canonical_type(self):
        return REQUEST_TYPES_DICT.get(self.type, '???')

    class Meta:
        unique_together = (('parent', 'type'),)

    def get_data(self):
        try:
            return loads(self.data)
        except ValueError:
            return None

    def set_data(self, data):
        self.data = dumps(data)

