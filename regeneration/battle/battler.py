#! /usr/bin/python
# Encoding: UTF-8

from fractions import Fraction
from collections import namedtuple
from functools import partial

from regeneration.battle.effect import EffectSubject
from regeneration.battle.stats import Stats
from regeneration.battle.move import Move

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Battler(EffectSubject):
    """A currently-sent-out monster.

    This class includes everything that can be set on a Monster in battle.
    It synchronizes whatever it should (HP, status, item changes) with the
    Monster, but keeps volatile things (stat/ability/move changes) to itself,
    to be forgotten when a battle ends.
    """
    forcedMove = None

    def __init__(self, monster, spot, loader):
        EffectSubject.__init__(self, spot.field)
        self.monster = monster
        self.species = monster.species
        self.spot = spot

        self.ability = monster.ability

        self.stats = Stats(monster.stats)
        self.statLevels = Stats(loader.battleStats)

        self.moves = list(monster.moves)

        self.level = monster.level
        self.types = monster.types

    @property
    def fainted(self):
        return self.hp <= 0

    @property
    def name(self):
        return self.monster.name

    @property
    def status(self):
        return self.monster.status

    @status.setter
    def status(self, value):
        self.monster.status = value

    @property
    def hp(self):
        return self.monster.hp

    @hp.setter
    def hp(self, value):
        self.monster.hp = value

    @property
    def tameness(self):
        return self.monster.tameness

    @property
    def gender(self):
        return self.monster.gender

    @property
    def item(self):
        return self.monster.item

    @item.setter
    def item(self, newItem):
        self.monster.item = newItem

    def setMove(self, i, kind):
        self.moves = list(self.moves)
        self.moves[i] = Move(kind)