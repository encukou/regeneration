#! /usr/bin/python
# Encoding: UTF-8

import random

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Gender(object):
    """ An enumeration of genders
    """
    def __init__(self, identifier, symbol, value):
        self.identifier = identifier
        self.symbol = symbol
        self.value = value

    @classmethod
    def random(cls, gender_rate, rand=random):
        if gender_rate == -1:
            # Ditto & Genderless
            return cls.none
        elif rand.randint(0, 7) < gender_rate:
            return cls.female
        else:
            return cls.male

    @classmethod
    def get(self, identifier):
        return getattr(self, identifier)

    def is_opposite(self, other):
        return self.value and self.value == -other.value

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return "<Gender: %s>" % self.identifier

Gender.none = Gender('none', u'–', 0)
Gender.male = Gender('male', u'♂', -1)
Gender.female = Gender('female', u'♀', 1)
