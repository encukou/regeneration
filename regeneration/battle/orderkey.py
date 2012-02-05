#! /usr/bin/env python
# Encoding: UTF-8

"""An extensible ordering key class

The goal of the OrderKey class is to have a sorted sequence of objects
which can act as sort keys, and to which items may be added at any time,
in any place, without disturbing the order of the original keys.
"""

# Currently implemented as a doubly-linked list, with Fraction ids for
# comparisons.

# Copyright (c) 2010, Petr Viktorin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written authorization.

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

from fractions import Fraction
import itertools

class OrderKeys(object):
    """An extensible ordering key class

    The goal of the OrderKeys class is to have a sorted sequence of objects
    which can act as sort keys, and to which items may be added at any time,
    in any place, without disturbing the order of the original keys.

    If is expected that some kind of plugins or a similar mechanism will add
    more keys at arbitrary places in the sequence.
    """
    def __init__(self, length=1):
        self.first = self.last = OrderKey(_keys=self)
        for i in range(length - 1):
            self.new_last()

    def new_first(self):
        """Create a new key that comes at the beginning and return it.
        """
        return self.first.new_before()

    def new_last(self):
        """Create a new key that comes at the end and return it.
        """
        return self.last.new_after()

    def __contains__(self, key):
        """Is the key in this sequence?"""
        try:
            return key.keys is self
        except AttributeError:
            return False

    def __iter__(self):
        """Iterate this equence"""
        yv = self.first
        while yv:
            yield yv
            yv = yv.next

    def __reversed__(self):
        """Iterate this sequence in reverse"""
        yv = self.last
        while yv:
            yield yv
            yv = yv.prev

class OrderKey(object):
    __slots__ = 'prev next keys id'.split()

    def __init__(self, _parent=None, _keys=None):
        """An order key. Not meant to be instantiated directly.
        """
        self.keys = _keys or _parent.keys
        if _parent is None:
            self.prev = self.next = None
            self.id = 0
        else:
            self.prev = _parent.prev
            self.next = _parent.next
            self.id = 0

    def new_before(self, number=None):
        """Create a new key that comes before this one and return it"""
        if number is not None:
            return list(reversed([self.new_before() for i in range(number)]))
        rv = OrderKey(self)
        rv.next = self
        prev = self.prev
        self.prev = rv
        if prev:
            prev.next = rv
            rv.id = Fraction(self.id + prev.id) / 2
        else:
            self.keys.first = rv
            rv.id = self.id - 1
        return rv

    def new_after(self, number=None):
        """Create a new key that comes after this one and return it"""
        if number is not None:
            return [self.new_after() for i in range(number)]
        rv = OrderKey(self)
        rv.prev = self
        next = self.next
        self.next = rv
        if next:
            next.prev = rv
            rv.id = Fraction(self.id + next.id) / 2
        else:
            self.keys.last = rv
            rv.id = self.id + 1
        return rv

    def __str__(self):
        """Create a string representation of this key.  NB, might surprise!

        NB: The 0-based numeric index given by this method is subject to
        change as new keys are added. It is also expensive to compute.
        Use only for debugging.
        """
        for i, obj in enumerate(self.keys):
            if obj is self:
                return '<OrderKey %s at 0x%x>' % (i, id(self))
    __repr__ = __str__

    def __gt__(self, other): return self.id > other.id
    def __ge__(self, other): return self.id >= other.id
    def __lt__(self, other): return self.id < other.id
    def __le__(self, other): return self.id <= other.id
