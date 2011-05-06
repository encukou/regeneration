#! /usr/bin/python
# Encoding: UTF-8

from itertools import chain, izip_longest

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import quiet, QuietTestCase

from regeneration.battle import moveeffect
from regeneration.battle import effect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

some_flags = set('spam eggs'.split())

class Object(object):
    pass

class EffectSubclass(effect.Effect):
    pass

class FakeField(effect.EffectSubject):
    def __init__(self):
        effect.EffectSubject.__init__(self, self)
        self.give_effect_self(EffectSubclass())  # for coverage

    def flip_coin(self, chance, blurb):
        return True

    def calculate_damage(self, hit):
        return hit.power / 2

class TestMoveEffectFlags(QuietTestCase):
    def test_flags_dict(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = dict.fromkeys(some_flags, True)

        assert SomeEffect.flags == some_flags

    def test_flags_set(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = some_flags

        assert SomeEffect.flags == some_flags

    def test_flags_list(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = list(some_flags)

        assert SomeEffect.flags == some_flags

    def test_inherit(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = some_flags

        class SomeOtherEffect(SomeEffect):
            flags = ['ham']

        assert SomeOtherEffect.flags == set(['ham']) | some_flags

    def test_unset(self):
        class SomeEffect(moveeffect.MoveEffect):
            flags = some_flags

        class SomeOtherEffect(SomeEffect):
            flags = dict(spam=False)

        assert SomeOtherEffect.flags == set(['eggs'])

@quiet
def test_nove_flag():
    assert str(moveeffect.MoveEffect.ppless) == 'ppless'
    assert 'move flag' in str(moveeffect.Flag())

class TestMoveEffect(QuietTestCase):
    def setup_method(self, m):
        super(TestMoveEffect, self).setup_method(m)
        self.field = FakeField()

        self.move = Object()
        self.move.power = 20
        self.move.type = Object()
        self.move.accuracy = 0.5
        self.move.damage_class = Object()
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

    def assert_changes(self, hp=40, pp=5):
        assert self.target.battler.hp == hp
        assert self.move.pp == pp

    def test_move_effect(self):
        self.moveeffect.begin_turn()
        (hit, ) = self.moveeffect.attempt_use()
        assert hit.damage == 10
        self.assert_changes(hp=30, pp=4)

    def test_copy_to_user(self):
        me = self.moveeffect.copy_to_user(self.user)
        me.begin_turn()
        (hit, ) = me.attempt_use()
        assert hit.damage == 10
        self.assert_changes(hp=30, pp=4)

    def test_prevent_use(self):
        effect = EffectSubclass()
        effect.prevent_use = lambda moveeffect: True
        self.field.give_effect_self(effect)
        assert self.moveeffect.attempt_use() == None
        self.assert_changes()

    def test_prevent_hit(self):
        effect = EffectSubclass()
        effect.prevent_hit = lambda hit: True
        self.field.give_effect_self(effect)
        assert self.moveeffect.attempt_use() == [None]
        self.assert_changes(pp=4)

    def test_miss(self):
        self.field.flip_coin = lambda prob, blurb: False
        assert self.moveeffect.attempt_use() == [None]
        self.assert_changes(pp=4)

    def test_no_accuracy(self):
        self.moveeffect.accuracy = None
        self.field.flip_coin = lambda prob, blurb: False
        (hit, ) = self.moveeffect.attempt_use()
        assert hit.damage == 10
        self.assert_changes(hp=30, pp=4)

    def test_multiple_targets(self):
        self.move.targetting.targets = lambda u, t: [t, self.user]
        (hitA, hitB) = self.moveeffect.attempt_use()
        assert hitA.damage == 10
        assert hitB.damage == 10
        assert hitA.target == self.target
        assert hitB.target == self.user
        self.assert_changes(hp=30, pp=4)
        assert self.user.battler.hp == 20
