#! /usr/bin/python
# Encoding: UTF-8

"""Helpers used in the tests
"""

import sys
import unittest
import yaml
import difflib
import traceback
from functools import wraps
from contextlib import contextmanager

import nose.tools

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

def assert_all_equal(head, *tail):  # not camelCase, to match nosetests API
    """Assert every argument is equal to the first
    """
    for i, item in enumerate(tail):
        assert_equal(head, item,
                'Item %d (%r) is not equal to %r' % (i + 1, item, head)
            )

class FakeRand(object):
    """A random-like object that mostly returns zeroes – not random at all!
    """
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
def quietContext():
    sys.stdout = logger = WriteLogger(sys.stdout)
    origStdout = sys.stdout
    yield
    sys.stdout = origStdout
    if logger.stack:
        print; print '-----'
        for line in logger.stack:
            print line.rstrip()
        print 'Test wrote to stdout'
        raise AssertionError('Test wrote to stdout')

def quiet(func):
    """Make sure the decorated test doesn't write to stdout
    """
    @wraps(func)
    def hushedTest(*args, **kwargs):
        with quietContext():
            func(*args, **kwargs)
    return hushedTest

class QuietTestCase(unittest.TestCase):
    def setUp(self):
        self.__quietContext = quietContext()
        self.__quietContext.__enter__()

    def tearDown(self):
        self.__quietContext.__exit__(None, None, None)

def assert_equal(a, b, *args, **kwargs):  # not camelCase to match nose
    """Like assert_equal, buts print a diff of yaml dumps to stdout on failure

    (stdout is chosen because nose displays it more conveniently)
    """
    try:
        nose.tools.assert_equal(a, b, *args, **kwargs)
    except Exception, e:
        try:
            print 'YAML diff (+first, -second)'
            for line in difflib.ndiff(
                    *(yaml.dump(x, default_flow_style=False).splitlines()
                            for x in (b, a)
                        )
                ):
                print line
        except:
            print 'Cannot print YAML dump'
        raise e
