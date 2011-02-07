#! /usr/bin/python
# Encoding: UTF-8

import random

from regeneration.battle.enum import Enum

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Stat(Enum):
    """ An enumeration of stats
    """
    # XXX: Use veekun DB objects; but handle BattleStat correctly
    identifiers = "hp atk def spd sat sde".split()
    names = "HP,Attack,Defense,Speed,Special Attack,Special Defense".split(',')


class BattleStat(Stat):
    identifiers = "acc eva".split()
    names = "Accuracy,Evasion".split(',')

for stat, name in zip(
        BattleStat,
        Stat.names + BattleStat.names,
    ):
    stat.name = name


class Stats(dict):
    """A collection of Stat values

    Basically a hybrid that supports both attribute and item access to get
    the values.
    Its keys are Enum objects.
    """
    _statEnum = Stat

    @classmethod
    def Random(cls, min, max, rand=random, statEnum=Stat):
        self = cls()
        self._statEnum = statEnum
        for stat in statEnum:
            self.addItem(stat, rand.randint(min, max))
        return self

    def __getitem__(self, item):
        try:
            return super(Stats, self).__getitem__(item)
        except KeyError:
            return super(Stats, self).__getitem__(self._statEnum[item])

    def __setitem__(self, item, value):
        """Setter. You can use Enum objects, numbers or names for item.

        Only pre-existing keys can be set using []. Use addItem() if you're
        sure you want to add a new item.
        """
        if not item in self:
            item = self._statEnum[item]
        super(Stats, self).__setitem__(item, value)

    def __getattr__(self, attr):
        return self[self._statEnum[attr]]

    def __setattr__(self, attr, value):
        if attr[:1] == '_':
            self.__dict__[attr] = value
        else:
            self[self._statEnum[attr.rstrip('_')]] = value

    def addItem(self, item, value):
        """As __setitem__, but allows setting keys that don't exist yet.

        Be sure to use a Enum object as the key, not ints/strings"""
        super(Stats, self).__setitem__(item, value)

    def __iter__(self):
        return (x[1] for x in sorted(self.items(), key=lambda x: x[0]))

    def __str__(self):
        return "<Stats: {"+", ".join(str(s)+": "+str(self[s]) for s in self._statEnum)+"}>"

    def save(self):
        return dict((k.identifier, v) for k, v in self.items())

    @classmethod
    def load(cls, dct):
        return cls(
                ([s for s in Stat if s.identifier==k][0], v)
                for k, v in dct.items()
            )

    def __deepcopy__(self, memo):
        return self.__class__(self)

