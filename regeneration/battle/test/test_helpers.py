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

class TestEnum(enum.Enum):
    identifiers = 'a b c d'.split()

@quiet
def testEnum():
    assert TestEnum.a.identifier == 'a'
    assert TestEnum.a < TestEnum.b
    assert TestEnum.a <= TestEnum.c
    assert TestEnum.d > TestEnum.a
    assert TestEnum.c >= TestEnum.b
    assert TestEnum.b != TestEnum.d
    assert TestEnum.c == TestEnum.c
    assert len(TestEnum) == 4
    assert TestEnum[0] == TestEnum.a
    assert TestEnum['b'] == TestEnum.b
    assert str(TestEnum.c) == 'c'
    assert 'e' in repr(TestEnum.d)

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

