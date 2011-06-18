#! /usr/bin/env python
# Encoding: UTF-8

from fractions import Fraction
from collections import namedtuple
from functools import partial

from regeneration.battle.effect import Effect, EffectSubject
from regeneration.battle.stats import Stats, StatAttributeAccessMixin
from regeneration.battle.move import Move
from regeneration.battle import messages

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class ComputedStats(StatAttributeAccessMixin):
    def __init__(self, battler):
        self._battler = battler

    def __getitem__(self, stat):
        return self._battler.get_stat(stat)

    def __iter__(self):
        return iter(self._battler.stat_levels)

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

        self.stats = ComputedStats(self)
        self.stat_levels = Stats(loader.battle_stats)

        self.moves = list(monster.moves)

        self.level = monster.level
        self.types = monster.types

        self.trainer = spot.trainer

        self.ability_effect = None
        self.ability = monster.ability

        self.item_effect = None
        self.item = monster.item

        self.used_move_effects = []

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

    def do_damage(self, damage, direct=False, message_class=messages.HPChange,
                **extra_message_args):
        Effect.damage_done(self, damage)
        self.change_hp(-damage, direct, message_class, **extra_message_args)

    def change_hp(self, delta, direct=False, message_class=messages.HPChange,
                **extra_message_args):
        self.hp += delta
        if self.hp > self.stats.hp:
            self.hp = self.stats.hp
        self.field.message(message_class, battler=self, direct=direct,
                delta=delta, hp=self.hp, **extra_message_args)
        if self.hp <= 0:
            self.field.message.Fainted(battler=self)
            self.status = 'fnt'

    def get_ability_effect(self):
        return None

    def get_item_effect(self):
        return None

    def get_stat(self, stat):
        if stat.identifier == 'hp':
            return self.monster.stats[stat]
        level = self.stat_levels[stat]
        if stat in self.monster.stats:
            base = self.monster.stats[stat]
            numerator = denominator = 2
            round_func = int
        else:
            base = 1
            numerator = denominator = 3
            round_func = Fraction
        if level < 0:
            denominator -= level
        elif level > 0:
            numerator += level
        value = round_func(base * Fraction(numerator, denominator))
        return Effect.modify_stat(self, value, stat)

    def raise_stat(self, stat, delta, verbose=True):
        previous = self.stat_levels[stat]
        result = self.stat_levels[stat] + delta
        if result > 6:
            result = 6
        elif result < -6:
            result = -6
        self.stat_levels[stat] = result
        real_delta = result - previous
        if verbose:
            direction = (delta > 0) - (delta < 0)
            self.field.message.StatChange(battler=self, stat=stat,
                    delta=real_delta, direction=direction)
        return real_delta

    def message_values(self, trainer):
        return dict(
                name=self.name,
                spot=self.spot.message_values(trainer),
            )

    def __repr__(self):
        return "<Battler: %s's %s>" % (self.trainer.name, self.monster)
