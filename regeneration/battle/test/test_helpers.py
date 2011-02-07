#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_equal, assert_raises, raises

from regeneration.battle.test import assert_all_equal, quiet

from regeneration.battle import enum
from regeneration.battle import stats
from regeneration.battle import gender

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def testStats():
    assert_equal(len(stats.Stat), 6)
    assert_equal(stats.Stat.sat.name, 'Special Attack')
    assert_equal(str(stats.Stat.def_), 'Defense')
    assert_equal(stats.Stat.sat.number, 4)
    assert_equal(
            [s.identifier for s in stats.Stat],
            'hp atk def spd sat sde'.split(),
        )

    assert stats.Stat.hp < stats.Stat.atk
    assert stats.Stat.hp <= stats.Stat.atk
    assert stats.Stat.sde > stats.Stat.atk
    assert stats.Stat.spd >= stats.Stat.hp
    assert stats.Stat.hp != stats.Stat.sat
    assert stats.Stat.hp == stats.Stat.hp

    assert_equal(len(stats.BattleStat), 8)
    assert_equal(
            [s.identifier for s in stats.BattleStat],
            'hp atk def spd sat sde acc eva'.split(),
        )

    assert_equal(
            [s.name for s in stats.Stat],
            'HP,Attack,Defense,Speed,Special Attack,Special Defense'.split(','),
        )

    class FakeRand():
        def randint(self, a, b):
            return a + b

    statdict = stats.Stats(2, 4, rand=FakeRand())
    assert_equal(list(statdict), [6] * 6)

    assert_all_equal(statdict['hp'], statdict[0], statdict[stats.Stat.hp], 6)

    statdict['hp'] = 7
    assert_all_equal(7, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(6, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict[1] = 8
    assert_all_equal(7, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(8, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict[stats.Stat.hp] = 9
    assert_all_equal(9, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(8, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict.atk = 10
    assert_all_equal(9, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(10, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    def setFoo():
        statdict['foo'] = 11
    assert_raises(KeyError, setFoo)

    assert_equal(
            str(statdict),
            '<Stats: {HP: 9, Attack: 10, Defense: 6, Speed: 6, '
                'Special Attack: 6, Special Defense: 6}>',
        )

    assert_equal(repr(stats.Stat.def_), '<Stat Defense>') 

@quiet
def testGenders():
    assert_equal(gender.Gender.male.symbol, u'♂')
    assert_equal(gender.Gender.female.opposite.symbol, u'♂')
    assert_equal(gender.Gender.male.opposite.symbol, u'♀')
    assert_equal(gender.Gender.none.symbol, u'–')
    assert_equal(gender.Gender.none.opposite, None)

    assert gender.Gender.male.isOpposite(gender.Gender.female)
    assert not gender.Gender.male.isOpposite(gender.Gender.male)
    assert not gender.Gender.none.isOpposite(gender.Gender.male)
    assert not gender.Gender.male.isOpposite(gender.Gender.none)

@raises(TypeError)
@quiet
def testEnumNoIdentifiers():
    class Bad(enum.Enum):
        pass

@raises(ValueError)
@quiet
def testEnumIdentifierString():
    class Bad(enum.Enum):
        identifiers = 'just one string'

