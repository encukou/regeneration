#! /usr/bin/env python
# Encoding: UTF-8

from itertools import chain, izip_longest

from regeneration.battle.example import loader
from regeneration.battle.test import QuietTestCase

from regeneration.battle import effect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class BaseTestEffect(effect.Effect):
    @effect.callback
    def append(self, subject, item):
        pass

    @effect.chain
    def count(self, subject, value):
        pass

class BlockingEffect(BaseTestEffect):
    def block_application(self, effect):
        if effect is not self:
            return True

class UnapplicableEffect(BaseTestEffect):
    def block_application(self, effect):
        return True

class RecordingEffect(BaseTestEffect):
    def __init__(self, results=None):
        if results is None:
            results = set()
        self.results = results

    def append(self, subject, item):
        self.results.add((item, self))

class OtherRecordingEffect(BaseTestEffect):
    def __init__(self, results = None):
        if results is None:
            results = set()
        self.results = results

    def append(self, subject, item):
        self.results.add((item, self))

class CountingEffect(BaseTestEffect):
    def count(self, subject, value):
        return value + 1

@effect.unique_effect
class UniqueEffect(BaseTestEffect):
    pass

class TestEffect(QuietTestCase):
    def setup_method(self, m):
        super(TestEffect, self).setup_method(m)
        self.fake_field = effect.EffectSubject(None)
        self.fake_field.field = self.fake_field
        self.subject_a = effect.EffectSubject(self.fake_field)
        self.subject_b = effect.EffectSubject(self.fake_field)
        self.fake_field.active_subsubjects = self.subject_a, self.subject_b

    def assert_active_effects(self, *effects):
        assert set(self.fake_field.active_effects) == set(effects)

    def test_emptiness(self):
        self.assert_active_effects()

    def test_simple_application(self):
        eff = effect.Effect()
        self.subject_a.give_effect(self.fake_field, eff)
        self.assert_active_effects(eff)

    def test_application_return_value(self):
        eff = effect.Effect()
        applied = self.subject_a.give_effect(self.subject_b, eff)
        assert eff.subject is self.subject_b
        assert eff.inducer is self.subject_a
        assert applied is eff

    def test_two_applications(self):
        eff_a = effect.Effect()
        eff_b = effect.Effect()
        self.subject_a.give_effect(self.subject_b, eff_a)
        self.subject_a.give_effect(self.subject_b, eff_b)
        self.assert_active_effects(eff_a, eff_b)

    def test_self_application(self):
        eff = effect.Effect()
        applied = self.subject_a.give_effect_self(eff)
        assert eff.subject is self.subject_a
        assert eff.inducer is self.subject_a
        assert applied is eff

    def test_removal(self):
        eff_a = self.subject_a.give_effect_self(effect.Effect())
        eff_b = self.subject_a.give_effect_self(effect.Effect())
        eff_b.remove()
        self.assert_active_effects(eff_a)

    def test_unapplicable(self):
        eff_a = self.subject_a.give_effect_self(UnapplicableEffect())
        assert eff_a == None
        self.assert_active_effects()

    def test_apply_none(self):
        eff_a = self.subject_a.give_effect_self(None)
        assert eff_a == None
        self.assert_active_effects()

    def test_blocker(self):
        blocker = self.subject_a.give_effect_self(BlockingEffect())
        self.assert_active_effects(blocker)
        eff_a = self.subject_a.give_effect_self(effect.Effect())
        assert eff_a == None
        self.assert_active_effects(blocker)

    def test_blocker_disabled(self):
        blocker = self.subject_a.give_effect_self(BlockingEffect())
        with blocker.disabled():
            eff_a = self.subject_a.give_effect_self(effect.Effect())
        assert eff_a != None
        self.assert_active_effects(blocker, eff_a)

    def test_blocker_reenabled(self):
        blocker = self.subject_a.give_effect_self(BlockingEffect())
        with blocker.disabled():
            pass
        eff_a = self.subject_a.give_effect_self(effect.Effect())
        assert eff_a == None
        self.assert_active_effects(blocker)

    def test_disable_nesting(self):
        blocker = self.subject_a.give_effect_self(BlockingEffect())
        with blocker.disabled():
            eff_a = self.subject_a.give_effect_self(effect.Effect())
            with blocker.disabled():
                eff_b = self.subject_a.give_effect_self(effect.Effect())
        unapplied = self.subject_a.give_effect_self(effect.Effect())
        self.assert_active_effects(blocker, eff_a, eff_b)

    def test_get_effects_all(self):
        eff_a = self.subject_a.give_effect_self(RecordingEffect())
        eff_b = self.subject_a.give_effect_self(OtherRecordingEffect())
        effC = self.subject_a.give_effect_self(effect.Effect())
        assert (
                set(self.subject_a.get_effects()) ==
                set([eff_a, eff_b, effC])
            )

    def test_get_effects_specific(self):
        eff_a = self.subject_a.give_effect_self(RecordingEffect())
        eff_b = self.subject_a.give_effect_self(OtherRecordingEffect())
        effC = self.subject_a.give_effect_self(effect.Effect())
        assert list(self.subject_a.get_effects(RecordingEffect)) == [eff_a]

    def test_get_effects_nonexisting(self):
        eff_a = self.subject_a.give_effect_self(RecordingEffect())
        eff_b = self.subject_a.give_effect_self(OtherRecordingEffect())
        effC = self.subject_a.give_effect_self(effect.Effect())
        assert list(self.subject_a.get_effects(BlockingEffect)) == []

    def test_get_effect_any(self):
        eff = self.subject_a.give_effect_self(RecordingEffect())
        assert self.subject_a.get_effect() == eff

    def test_get_effect_specfic(self):
        eff_a = self.subject_a.give_effect_self(effect.Effect())
        eff_b = self.subject_a.give_effect_self(RecordingEffect())
        assert self.subject_a.get_effect(RecordingEffect) == eff_b

    def test_get_effect_nonexisting(self):
        eff = self.subject_a.give_effect_self(RecordingEffect())
        assert self.subject_a.get_effect(OtherRecordingEffect) == None

    def test_reparent(self):
        eff = self.subject_a.give_effect_self(effect.Effect())
        eff.reparent(self.subject_b)
        assert eff.inducer is self.subject_a
        assert eff.subject is self.subject_b
        assert list(self.subject_a.get_effects()) == []
        assert list(self.subject_b.get_effects()) == [eff]

    def test_str(self):
        assert 'RecordingEffect' in str(RecordingEffect())

    def test_repr(self):
        assert 'RecordingEffect' in repr(RecordingEffect())

    def test_unique_effect(self):
        uniq = self.fake_field.give_effect_self(UniqueEffect())
        assert set(self.fake_field.active_effects) == set([uniq])
        assert self.fake_field.give_effect_self(UniqueEffect()) == None
        assert set(self.fake_field.active_effects) == set([uniq])

    def test_chaining(self):
        assert BaseTestEffect.count(self.subject_a, 0) == 0
        self.subject_b.give_effect_self(CountingEffect())
        assert BaseTestEffect.count(self.subject_a, 0) == 1
        self.subject_b.give_effect_self(CountingEffect())
        assert BaseTestEffect.count(self.subject_a, 0) == 2
