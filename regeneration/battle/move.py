#! /usr/bin/env python
# Encoding: UTF-8

from fractions import Fraction

from regeneration.battle.moveeffect import MoveEffect
from regeneration.battle.movetargetting import MoveTargetting

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Move(object):
    """ Represents an individual move

    An individual move knows about the move type (i.e. the dex entry),
    and the max & current PP.

    The move doesn't store information about the monster that has it.
    That is the monster's responsibility.

    Anything that is reset after switching out is not included here.
    """

    def __init__(self, kind, maxpp=None):
        """ Create a move.

        By default, the new move will have non-PP-upped max PP.
        Current PP is set to the max on instantiation.
        """
        if maxpp is None:
            maxpp = kind.pp

        self.kind = kind
        self.pp = self.maxpp = maxpp

        self.targetting = self.get_targetting(kind.target.identifier)

        if kind.effect_chance:
            self.secondary_effect_chance = Fraction(kind.effect_chance, 100)
        else:
            self.secondary_effect_chance = None

        # We like convenient-er accessors to common things
        self.flags = MoveFlags(kind)

    def get_targetting(self, identifier):
        return MoveTargetting.by_identifier(identifier)

    def __str__(self):
        return "%s (%s/%s PP)" % (self.kind.identifier, self.pp, self.maxpp)

    @property
    def damage_class(self):
        return self.kind.damage_class

    @property
    def priority(self):
        return self.kind.priority

    @property
    def name(self):
        return self.kind.name

    @property
    def accuracy(self):
        if not self.kind.accuracy:
            return None
        else:
            return Fraction(self.kind.accuracy, 100)

    @property
    def power(self):
        if self.kind.power > 1:
            return self.kind.power
        else:
            return None

    @property
    def type(self):
        return self.kind.type

    def message_values(self, trainer):
        return dict(
                name=self.name,
                identifier=self.kind.identifier,
            )

    def get_effect(self, user, target):
        return MoveEffect(self, user, target)

class MoveFlags(object):
    def __init__(self, kind):
        self.kind = kind
        self.ppless = False

    def __getattr__(self, attrname):
        for flag in self.kind.flags:
            if flag.identifier == attrname:
                return True
        return False
