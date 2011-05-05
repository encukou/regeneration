#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_equal, assert_raises, raises

from regeneration.battle.test import assert_all_equal, quiet

from regeneration.battle import stats
from regeneration.battle import gender

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def testGenders():
    assert_equal(gender.Gender.male.symbol, u'♂')
    assert_equal(gender.Gender.none.symbol, u'–')

    assert gender.Gender.male.isOpposite(gender.Gender.female)
    assert not gender.Gender.male.isOpposite(gender.Gender.male)
    assert not gender.Gender.none.isOpposite(gender.Gender.male)
    assert not gender.Gender.male.isOpposite(gender.Gender.none)
