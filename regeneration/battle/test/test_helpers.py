#! /usr/bin/python
# Encoding: UTF-8

from regeneration.battle.test import quiet

from regeneration.battle import stats
from regeneration.battle import gender

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def test_genders():
    assert gender.Gender.male.symbol == u'♂'
    assert gender.Gender.none.symbol == u'–'

    assert gender.Gender.male.is_opposite(gender.Gender.female)
    assert not gender.Gender.male.is_opposite(gender.Gender.male)
    assert not gender.Gender.none.is_opposite(gender.Gender.male)
    assert not gender.Gender.male.is_opposite(gender.Gender.none)
