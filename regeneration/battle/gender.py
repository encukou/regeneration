#! /usr/bin/python
# Encoding: UTF-8

import random

from regeneration.battle.enum import Enum

__copyright__ = "Copyright 2009-2011, Petr Viktorin"
__license__ = "MIT"
__email__ = "encukou@gmail.com"

class Gender(Enum):
    """ An enumeration of genders
    """
    identifiers = 'none male female'.split()
    symbols = u'–♂♀'

    @classmethod
    def Random(cls, gender_rate, rand=random):
        if gender_rate == -1:
            # Ditto & Genderless
            return cls.none
        elif rand.randint(0, 7) < gender_rate:
            return cls.female
        else:
            return cls.male

    def isOpposite(self, other):
        if self.opposite and self.opposite == other:
            return True
        else:
            return False

for g, symbol, opposite in zip(
        Gender,
        Gender.symbols,
        [None, Gender.female, Gender.male]
    ):
    g.symbol = symbol
    g.opposite = opposite

