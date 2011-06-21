#! /usr/bin/env python
# Encoding: UTF-8

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

from regeneration.battle.effect import Effect
from fractions import Fraction

class _MoveEffectMetaclass(type):
    def __init__(cls, name, bases, dct):
        newFlags = dct.pop('flags', set())
        super(_MoveEffectMetaclass, cls).__init__(name, bases, dct)
        flags = set()
        for superclass in reversed(cls.mro()):
            if isinstance(superclass, _MoveEffectMetaclass) and (
                    superclass is not cls
                ):
                flags.update(superclass.flags)
        try:
            items = newFlags.items()
        except AttributeError:
            flags.update(newFlags)
        else:
            for key, value in items:
                if value:
                    flags.add(key)
                else:
                    flags.remove(key)
        # XXX: This is a class attribute; make it immutable!
        cls.flags = frozenset(flags)

class Flag(object):
    """A move flag
    """
    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        if self.name:
            return self.name
        else:
            return 'move flag at 0x%x' % id(self)

class MoveEffect(object):
    """An effect of a particular use of a move.
    """
    __metaclass__ = _MoveEffectMetaclass

    ppless = Flag('ppless')

    def __init__(self, move, user, target):
        self.move = move
        self.power = move.power
        self.field = user.field
        self.user = user
        self.target = target
        self.type = move.type
        self.accuracy = move.accuracy
        self.damage_class = move.damage_class
        self.targetting = move.targetting
        self.secondary_effect_chance = move.secondary_effect_chance

        if move.pp is None:
            self.flags = self.flags.union([self.ppless])

    def begin_turn(self):
        """Called at the beginning of a turn"""
        return None

    def copy_to_user(self, user):
        return type(self)(self.move, user, self.target)

    def fail(self, hit=None):
        """Signals failure"""
        self.field.message.Failed(moveeffect=self)

    def miss(self, hit):
        """Move missed"""
        if self.targetting.single_target:
            self.field.message.Miss(hit=hit)
        else:
            self.field.message.Avoid(hit=hit)
        return

    def attempt_use(self, **kwargs):
        if Effect.prevent_use(self):
            return
        return self.do_use()

    def do_use(self, **kwargs):
        self.field.message.UseMove(battler=self.user, moveeffect=self)
        Effect.move_used(self)
        self.targets = list(self.get_targets(**kwargs))
        self.deduct_pp()
        self.user.used_move_effects.append(self)
        hits = self.use(**kwargs)
        return hits

    def use(self, **kwargs):
        self.targets = list(self.targets)
        hits = list(self.hits(**kwargs))
        if not hits:
            self.field.message.NoTarget(moveeffect=self)
        else:
            return [self.attempt_hit(hit) for hit in hits]

    def hits(self, **kwargs):
        for target in self.targets:
            yield Hit(self, target, **kwargs)

    def get_targets(self, **kwargs):
        if self.target:
            target = self.target.spot.battler
        else:
            target = None
        for target in self.targetting.targets(self, target):
            if self.targettable(target, **kwargs):
                yield target

    def targettable(self, target, **kwargs):
        return not target.fainted

    def attempt_hit(self, hit):
        if Effect.prevent_hit(hit):
            return self.fail(hit)
        elif not self.roll_accuracy(hit):
            return self.miss(hit)
        return self.do_hit(hit)

    def roll_accuracy(self, hit):
        if hit.accuracy is None or Effect.ensure_hit(hit):
            return True
        else:
            accuracy = Effect.modify_accuracy(hit, hit.accuracy)
            return self.field.flip_coin(accuracy, 'Determine hit')

    def do_hit(self, hit):
        Effect.move_hit(hit)
        return self.hit(hit)

    def hit(self, hit):
        if self.power:
            if not self.do_damage(hit):
                return None
        if self.secondary_effect_chance:
            self.attempt_secondary_effect(hit)
        return hit

    def do_damage(self, hit):
        hit.damage = self.calculate_damage(hit)
        if hit.damage:
            hit.damage = hit.target.do_damage(hit.damage, direct=True)
            Effect.move_damage_done(hit)
        return hit.damage

    def calculate_damage(self, hit):
        # This is too mechanic-specific to have in MoveEffect
        return self.field.calculate_damage(hit)

    def attempt_secondary_effect(self, hit):
        chance = Effect.modify_secondary_chance(hit,
                self.secondary_effect_chance)
        if self.field.flip_coin(chance, 'Attempt secondary effect'):
            self.do_secondary_effect(hit)

    def do_secondary_effect(self, hit):
        pass

    def deduct_pp(self):
        if self.ppless not in self.flags:
            delta = -min(self.move.pp, Effect.pp_reduction(self, 1))
            self.move.pp += delta
            self.field.message.PPChange(move=self.move, battler=self.user,
                    delta=delta, pp=self.move.pp, cause=self)

    def determine_critical_hit(self, hit):
        stage = Effect.critical_hit_stage(hit, 1)
        rate = {
                1: Fraction(1, 16),
                2: Fraction(1, 8),
                3: Fraction(1, 4),
                4: Fraction(1, 3),
                5: Fraction(1, 2),
            }[min(stage, 5)]
        hit.is_critical = self.field.flip_coin(rate, 'Determine critical hit')
        if not hit.is_critical:
            hit.is_critical = Effect.force_critical_hit(self)

    def message_values(self, trainer):
        if trainer == self.user.trainer and self.target:
            target = self.target.message_values(trainer)
        else:
            target = None
        return dict(
                move=self.move.message_values(trainer),
                user=self.user.message_values(trainer),
                target=target,
            )

class Hit(object):
    def __init__(self, move_effect, target, **kwargs):
        self.move_effect = move_effect
        self.target = target
        self.field = move_effect.field
        self.user = move_effect.user
        self.type = move_effect.type
        self.accuracy = move_effect.accuracy
        self.damage_class = move_effect.damage_class
        self.args = kwargs
        self.effectivity = self._get_effectivity()
        if move_effect.power is None:
            self.power = None
        else:
            self.power = Effect.modify_base_power(self, move_effect.power)

    def _get_effectivity(self):
        if not self.type:
            return 1
        effectivity = 1
        efficacies = self.type.damage_efficacies
        for type in self.target.types:
            efficacy, = [e for e in efficacies if e.target_type == type]
            effectivity *= Fraction(efficacy.damage_factor, 100)
        return Effect.modify_effectivity(self, effectivity)

    def message_values(self, trainer):
        return dict(
                moveeffect=self.move_effect.message_values(trainer),
                target=self.target.message_values(trainer),
            )
