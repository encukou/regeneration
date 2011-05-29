#! /usr/bin/env python
# Encoding: UTF-8

"""Helpers used in the tests
"""

import sys
import yaml
import difflib
import traceback
from functools import wraps
from contextlib import contextmanager

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class FakeRand(object):
    """A random-like object that mostly returns zeroes – not random at all!
    """
    def random(self):
        return 0.0

    def randint(self, a, b):
        return 0

    def choice(self, lst):
        return lst[0]

    def shuffle(self, lst):
        lst.reverse()

class WriteLogger():
    def __init__(self, origstream):
        self.origstream = origstream
        self.stack = []

    def write(self, str):
        self.origstream.write(str)
        if not self.stack:
            self.stack = traceback.format_stack()[:-1]

@contextmanager
def quiet_context():
    sys.stdout = logger = WriteLogger(sys.stdout)
    orig_stdout = sys.stdout
    yield
    sys.stdout = orig_stdout
    if logger.stack:
        print
        print '-----'
        for line in logger.stack:
            print line.rstrip()
        print 'Test wrote to stdout'
        raise AssertionError('Test wrote to stdout')

def quiet(func):
    """Make sure the decorated test doesn't write to stdout
    """
    @wraps(func)
    def hushed_test(*args, **kwargs):
        with quiet_context():
            func(*args, **kwargs)
    return hushed_test

class QuietTestCase(object):
    def setup_method(self, m):
        self.__quiet_context = quiet_context()
        self.__quiet_context.__enter__()

    def teardown_method(self, m):
        self.__quiet_context.__exit__(None, None, None)
