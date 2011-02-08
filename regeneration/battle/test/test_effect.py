#! /usr/bin/python
# Encoding: UTF-8

from itertools import chain, izip_longest

from nose.tools import assert_raises, raises

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import QuietTestCase, assert_equal

from regeneration.battle import effect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class BlockingEffect(effect.Effect):
    @effect.callback
    def blockApplication(self, effect):
        if effect is not self:
            return True

class UnapplicableEffect(effect.Effect):
    @effect.callback
    def blockApplication(self, effect):
        return True

class RecordingEffect(effect.Effect):
    def __init__(self, results=None):
        if results is None:
            results = set()
        self.results = results

    @effect.callback
    def append(self, subject, item):
        self.results.add((item, self))

class OtherRecordingEffect(effect.Effect):
    def __init__(self, results = None):
        if results is None:
            results = set()
        self.results = results

    @effect.callback
    def append(self, subject, item):
        self.results.add((item, self))

class CountingEffect(effect.Effect):
    @effect.chain
    def count(self, subject, value):
        return value + 1

@effect.uniqueEffect
class UniqueEffect(effect.Effect):
    pass

class TestEffect(QuietTestCase):
    def setUp(self):
        super(TestEffect, self).setUp()
        self.fakeField = effect.EffectSubject(None)
        self.fakeField.field = self.fakeField
        self.subjectA = effect.EffectSubject(self.fakeField)
        self.subjectB = effect.EffectSubject(self.fakeField)
        self.fakeField.activeSubSubjects = self.subjectA, self.subjectB

    def assertActiveEffects(self, *effects):
        assert_equal(set(self.fakeField.activeEffects), set(effects))

    def testEmptiness(self):
        self.assertActiveEffects()

    def testSimpleApplication(self):
        eff = effect.Effect()
        self.subjectA.giveEffect(self.fakeField, eff)
        self.assertActiveEffects(eff)

    def testApplicationReturnValue(self):
        eff = effect.Effect()
        applied = self.subjectA.giveEffect(self.subjectB, eff)
        assert eff.subject is self.subjectB
        assert eff.inducer is self.subjectA
        assert applied is eff

    def testTwoApplications(self):
        effA = effect.Effect()
        effB = effect.Effect()
        self.subjectA.giveEffect(self.subjectB, effA)
        self.subjectA.giveEffect(self.subjectB, effB)
        self.assertActiveEffects(effA, effB)

    def testSelfApplication(self):
        eff = effect.Effect()
        applied = self.subjectA.giveEffectSelf(eff)
        assert eff.subject is self.subjectA
        assert eff.inducer is self.subjectA
        assert applied is eff

    def testRemoval(self):
        effA = self.subjectA.giveEffectSelf(effect.Effect())
        effB = self.subjectA.giveEffectSelf(effect.Effect())
        effB.remove()
        self.assertActiveEffects(effA)

    def testUnapplicable(self):
        effA = self.subjectA.giveEffectSelf(UnapplicableEffect())
        assert_equal(effA, None)
        self.assertActiveEffects()

    def testApplyNone(self):
        effA = self.subjectA.giveEffectSelf(None)
        assert_equal(effA, None)
        self.assertActiveEffects()

    def testBlocker(self):
        blocker = self.subjectA.giveEffectSelf(BlockingEffect())
        self.assertActiveEffects(blocker)
        effA = self.subjectA.giveEffectSelf(effect.Effect())
        assert_equal(effA, None)
        self.assertActiveEffects(blocker)

    def testBlockerDisabled(self):
        blocker = self.subjectA.giveEffectSelf(BlockingEffect())
        with blocker.disabled():
            effA = self.subjectA.giveEffectSelf(effect.Effect())
        assert effA != None
        self.assertActiveEffects(blocker, effA)

    def testBlockerReenabled(self):
        blocker = self.subjectA.giveEffectSelf(BlockingEffect())
        with blocker.disabled():
            pass
        effA = self.subjectA.giveEffectSelf(effect.Effect())
        assert_equal(effA, None)
        self.assertActiveEffects(blocker)

    def testDisableNesting(self):
        blocker = self.subjectA.giveEffectSelf(BlockingEffect())
        with blocker.disabled():
            effA = self.subjectA.giveEffectSelf(effect.Effect())
            with blocker.disabled():
                effB = self.subjectA.giveEffectSelf(effect.Effect())
        unapplied = self.subjectA.giveEffectSelf(effect.Effect())
        self.assertActiveEffects(blocker, effA, effB)

    def testGetEffectsAll(self):
        effA = self.subjectA.giveEffectSelf(RecordingEffect())
        effB = self.subjectA.giveEffectSelf(OtherRecordingEffect())
        effC = self.subjectA.giveEffectSelf(effect.Effect())
        assert_equal(
                set(self.subjectA.getEffects()),
                set([effA, effB, effC])
            )

    def testGetEffectsSpecific(self):
        effA = self.subjectA.giveEffectSelf(RecordingEffect())
        effB = self.subjectA.giveEffectSelf(OtherRecordingEffect())
        effC = self.subjectA.giveEffectSelf(effect.Effect())
        assert_equal(list(self.subjectA.getEffects(RecordingEffect)), [effA])

    def testGetEffectsNonexisting(self):
        effA = self.subjectA.giveEffectSelf(RecordingEffect())
        effB = self.subjectA.giveEffectSelf(OtherRecordingEffect())
        effC = self.subjectA.giveEffectSelf(effect.Effect())
        assert_equal(list(self.subjectA.getEffects(BlockingEffect)), [])

    def testGetEffectAny(self):
        eff = self.subjectA.giveEffectSelf(RecordingEffect())
        assert_equal(self.subjectA.getEffect(), eff)

    def testGetEffectSpecfic(self):
        effA = self.subjectA.giveEffectSelf(effect.Effect())
        effB = self.subjectA.giveEffectSelf(RecordingEffect())
        assert_equal(self.subjectA.getEffect(RecordingEffect), effB)

    def testGetEffectNonexisting(self):
        eff = self.subjectA.giveEffectSelf(RecordingEffect())
        assert_equal(self.subjectA.getEffect(OtherRecordingEffect), None)

    def testReparent(self):
        eff = self.subjectA.giveEffectSelf(effect.Effect())
        eff.reparent(self.subjectB)
        assert eff.inducer is self.subjectA
        assert eff.subject is self.subjectB
        assert_equal(list(self.subjectA.getEffects()), [])
        assert_equal(list(self.subjectB.getEffects()), [eff])

    def testGoodCall(self):
        results = set()
        effA = self.subjectA.giveEffectSelf(RecordingEffect(results))
        effB = self.subjectA.giveEffectSelf(OtherRecordingEffect(results))
        RecordingEffect.append(self.subjectB, 'abc')
        assert_equal(results, set([('abc', effA)]))
        OtherRecordingEffect.append(self.subjectB, 'def')
        assert_equal(results, set([('abc', effA), ('def', effB)]))

    def testStr(self):
        assert 'RecordingEffect' in str(RecordingEffect())

    def testRepr(self):
        assert 'RecordingEffect' in repr(RecordingEffect())

    def testUniqueEffect(self):
        uniq = self.fakeField.giveEffectSelf(UniqueEffect())
        assert_equal(set(self.fakeField.activeEffects), set([uniq]))
        assert_equal(self.fakeField.giveEffectSelf(UniqueEffect()), None)
        assert_equal(set(self.fakeField.activeEffects), set([uniq]))

    def testChaining(self):
        assert_equal(CountingEffect.count(self.subjectA, 0), 0)
        self.subjectB.giveEffectSelf(CountingEffect())
        assert_equal(CountingEffect.count(self.subjectA, 0), 1)
        self.subjectB.giveEffectSelf(CountingEffect())
        assert_equal(CountingEffect.count(self.subjectA, 0), 2)
