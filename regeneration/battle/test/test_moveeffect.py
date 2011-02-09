#! /usr/bin/python
# Encoding: UTF-8

from itertools import chain, izip_longest

from nose.tools import assert_raises, raises

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import quiet, QuietTestCase, assert_equal

from regeneration.battle import moveeffect
from regeneration.battle import effect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

someFlags = set('spam eggs'.split())

class Object(object):
    pass

class EffectSubclass(effect.Effect):
    pass

class FakeField(effect.EffectSubject):
    def __init__(self):
        effect.EffectSubject.__init__(self, self)
        self.giveEffectSelf(EffectSubclass())  # for coverage

    def flipCoin(self, chance, blurb):
        return True

    def calculateDamage(self, hit):
        return hit.power / 2

class TestMoveEffectFlags(QuietTestCase):
    def testFlagsDict(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = dict.fromkeys(someFlags, True)

        assert_equal(SomeEffect.flags, someFlags)

    def testFlagsSet(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = someFlags

        assert_equal(SomeEffect.flags, someFlags)

    def testFlagsList(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = list(someFlags)

        assert_equal(SomeEffect.flags, someFlags)

    def testInherit(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = someFlags

        class SomeOtherEffect(SomeEffect):
            flags = ['ham']

        assert_equal(SomeOtherEffect.flags, set(['ham']) | someFlags)

    def testUnset(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = someFlags

        class SomeOtherEffect(SomeEffect):
            flags = dict(spam=False)

        assert_equal(SomeOtherEffect.flags, set(['eggs']))

@quiet
def testMoveFlag():
    assert_equal(str(moveeffect.MoveEffect.ppless), 'ppless')
    assert('move flag' in str(moveeffect.Flag()))

class TestMoveEffect(QuietTestCase):
    def setUp(self):
        super(TestMoveEffect, self).setUp()
        self.field = FakeField()

        self.move = Object()
        self.move.power = 20
        self.move.type = Object()
        self.move.accuracy = 0.5
        self.move.damageClass = Object()
        self.move.targetting = Object()
        self.move.targetting.targets = lambda u, t: [t]
        self.move.pp = 5

        self.user = Object()
        self.user.field = self.field
        self.user.battler = Object()
        self.user.battler.fainted = False
        self.user.battler.hp = 30

        self.target = Object()
        self.target.field = self.field
        self.target.battler = Object()
        self.target.battler.fainted = False
        self.target.battler.hp = 40

        self.moveeffect = moveeffect.MoveEffect(
                field=self.field,
                move=self.move,
                user=self.user,
                target=self.target,
            )

    def assertChanges(self, hp=40, pp=5):
        assert_equal(self.target.battler.hp, hp)
        assert_equal(self.move.pp, pp)

    def testMoveEffect(self):
        self.moveeffect.beginTurn()
        (hit, ) = self.moveeffect.attemptUse()
        assert_equal(hit.damage, 10)
        self.assertChanges(hp=30, pp=4)

    def testCopyToUser(self):
        me = self.moveeffect.copyToUser(self.user)
        me.beginTurn()
        (hit, ) = me.attemptUse()
        assert_equal(hit.damage, 10)
        self.assertChanges(hp=30, pp=4)

    def testPreventUse(self):
        effect = EffectSubclass()
        effect.preventUse = lambda moveeffect: True
        self.field.giveEffectSelf(effect)
        assert_equal(self.moveeffect.attemptUse(), None)
        self.assertChanges()

    def testPreventHit(self):
        effect = EffectSubclass()
        effect.preventHit = lambda hit: True
        self.field.giveEffectSelf(effect)
        assert_equal(self.moveeffect.attemptUse(), [None])
        self.assertChanges(pp=4)

    def testMiss(self):
        self.field.flipCoin = lambda prob, blurb: False
        assert_equal(self.moveeffect.attemptUse(), [None])
        self.assertChanges(pp=4)

    def testNoAccuracy(self):
        self.moveeffect.accuracy = None
        self.field.flipCoin = lambda prob, blurb: False
        (hit, ) = self.moveeffect.attemptUse()
        assert_equal(hit.damage, 10)
        self.assertChanges(hp=30, pp=4)

    def testMultipleTargets(self):
        self.move.targetting.targets = lambda u, t: [t, self.user]
        (hitA, hitB) = self.moveeffect.attemptUse()
        assert_equal(hitA.damage, 10)
        assert_equal(hitB.damage, 10)
        assert_equal(hitA.target, self.target)
        assert_equal(hitB.target, self.user)
        self.assertChanges(hp=30, pp=4)
        assert_equal(self.user.battler.hp, 20)
