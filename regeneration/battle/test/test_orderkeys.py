#! /usr/bin/env python
# Encoding: UTF-8

from regeneration.battle.test import QuietTestCase
from regeneration.battle.orderkey import OrderKeys

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class TestOrderKeys(QuietTestCase):
    def check(self, keys, k1, k2, k3, k4):
        assert k1 < k2 < k3 < k4
        assert k1 <= k2 <= k3 <= k4
        assert k4 > k3 > k2 > k1
        assert k4 >= k3 >= k2 >= k1
        assert k1 != k2 != k3 != k4
        assert [k1, k2, k3, k4] == list(keys)
        assert [k4, k3, k2, k1] == list(reversed(keys))
        for k in keys:
            assert k in keys

    def test_creation(self):
        keys = k1, k2, k3, k4 = OrderKeys(4)
        self.check(keys, k1, k2, k3, k4)

    def test_add_last(self):
        keys = k1, k2, k3 = OrderKeys(3)
        k4 = keys.new_last()
        self.check(keys, k1, k2, k3, k4)

    def test_add_after(self):
        keys = k1, k2, k4 = OrderKeys(3)
        k3 = k2.new_after()
        self.check(keys, k1, k2, k3, k4)

    def test_add_after_last(self):
        keys = k1, k2, k3 = OrderKeys(3)
        k4 = k3.new_after()
        self.check(keys, k1, k2, k3, k4)

    def test_add_first(self):
        keys = k2, k3, k4 = OrderKeys(3)
        k1 = keys.new_first()
        self.check(keys, k1, k2, k3, k4)

    def test_add_before(self):
        keys = k1, k2, k4 = OrderKeys(3)
        k3 = k4.new_before()
        self.check(keys, k1, k2, k3, k4)

    def test_add_before_first(self):
        keys = k2, k3, k4 = OrderKeys(3)
        k1 = k2.new_before()
        self.check(keys, k1, k2, k3, k4)
