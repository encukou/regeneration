#! /usr/bin/env python
# Encoding: UTF-8

from fractions import Fraction
from collections import namedtuple
from functools import partial

from regeneration.battle.effect import Effect, EffectSubject
from regeneration.battle.stats import Stats
from regeneration.battle.move import Move
from regeneration.battle import messages

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
    def __init__(self, monster, spot, loader):
        EffectSubject.__init__(self, spot.field)
        self.monster = monster
        self.species = monster.species
        self.spot = spot

        self.ability_effect = None
        self.ability = monster.ability

        self.stats = Stats(monster.stats)
        self.stat_levels = Stats(loader.battle_stats)

        self.moves = list(monster.moves)

        self.level = monster.level
        self.types = monster.types

        self.trainer = spot.trainer

        self.item_effect = None
        self.item = self.item

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
    def item(self, new_item):
        self.monster.item = new_item
        if self.item_effect:
            self.item_effect.remove()
        self.item_effect = self.give_effect_self(self.get_item_effect())

    @property
    def ability(self):
        return self._ability

    @ability.setter
    def ability(self, new_ability):
        self._ability = new_ability
        if self.ability_effect:
            self.ability_effect.remove()
        self.ability_effect = self.give_effect_self(self.get_ability_effect())

    @property
    def opponents(self):
        return [battler for battler in self.field.battlers
                if battler.spot.side != self.spot.side]

    @property
    def allies(self):
        return [battler for battler in self.field.battlers
                if battler.spot.side == self.spot.side and battler is not self]

    def set_move(self, i, kind):
        self.moves = list(self.moves)
        self.moves[i] = Move(kind)

    def do_damage(self, damage, direct=False, message_class=messages.HPChange):
        self.hp -= damage
        Effect.damage_done(self, damage)
        self.field.message(message_class, battler=self, direct=direct,
                delta=-damage, hp=self.hp)
        if self.hp <= 0:
            self.field.message.Fainted(battler=self)

    def get_ability_effect(self):
        return None

    def get_item_effect(self):
        return None

    def message_values(self, trainer):
        hp_fraction = Fraction(self.hp, self.stats.hp).limit_denominator(48)
        if trainer == self.trainer:
            hp = self.hp
        else:
            hp = None
        return dict(
                id=id(self.monster),
                name=self.name,
                hp_fraction=[hp_fraction.numerator, hp_fraction.denominator],
                hp=hp,
                spot=self.spot.message_values(trainer)
            )

    def __repr__(self):
        return "<Battler: %s's %s>" % (self.trainer.name, self.monster)
