#! /usr/bin/env python
# Encoding: UTF-8

from fractions import Fraction

from regeneration.battle.effect import Effect, EffectSubject
from regeneration.battle import orderkeys

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class DamagePlus2(Effect):
    @Effect.orderkey(orderkeys.mod2.new_before())
    def modify_move_damage(self, target, damage, hit):
        return damage + 2

class CriticalHitModifier(Effect):
    @Effect.orderkey(orderkeys.mod2.new_before())
    def modify_move_damage(self, target, damage, hit):
        if hit.is_critical:
            return damage * 2
        else:
            return damage

class RandomizeDamage(Effect):
    @Effect.orderkey(orderkeys.mod3.new_before())
    def modify_move_damage(self, target, damage, hit):
        damage *= target.field.randint(217, 255, 'Randomizing move damage')
        damage *= 100
        damage = int(damage / 255)
        damage /= 100
        return damage

class DamageStabModifier(Effect):
    @Effect.orderkey(orderkeys.mod3.new_before())
    def modify_move_damage(self, target, damage, hit):
        if hit.type in hit.user.types:
            return int(damage * Fraction(3, 2))
        else:
            return damage

class DamageEffectivityModifier(Effect):
    @Effect.orderkey(orderkeys.mod3.new_before())
    def modify_move_damage(self, target, damage, hit):
        return int(damage * hit.effectivity)

default_effect_classes = [DamagePlus2, CriticalHitModifier, RandomizeDamage,
        DamageStabModifier, DamageEffectivityModifier]
