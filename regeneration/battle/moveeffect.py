#! /usr/bin/env python
# Encoding: UTF-8

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

from regeneration.battle.effect import Effect

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

    def __init__(self, field, move, user, target):
        self.move = move
        self.power = move.power
        self.field = field
        self.user = user
        self.target = target
        self.type = move.type
        self.accuracy = move.accuracy
        self.damage_class = move.damage_class
        self.targetting = move.targetting

        if move.pp is None:
            self.flags = self.flags.union([self.ppless])

    def begin_turn(self):
        """Called at the beginning of a turn"""
        return None

    def copy_to_user(self, user):
        return type(self)(self.field, self.move, user, self.target)

    def fail(self, hit=None):
        """Signals failure"""
        return

    def attempt_use(self, **kwargs):
        if Effect.prevent_use(self):
            return self.fail()
        return self.do_use()

    def do_use(self, **kwargs):
        self.field.message.UseMove(battler=self.user, moveeffect=self)
        self.deduct_pp()
        return self.use(**kwargs)

    def use(self, **kwargs):
        self.hits = [hit for hit in self.hits(**kwargs)]
        return [self.attempt_hit(hit) for hit in self.hits]

    def hits(self, **kwargs):
        for target in self.targets(**kwargs):
            if self.targettable(target, **kwargs):
                yield Hit(self, target, **kwargs)

    def targets(self, **kwargs):
        return self.targetting.targets(self, self.target)

    def targettable(self, target, **kwargs):
        return not target.battler.fainted

    def attempt_hit(self, hit):
        if Effect.prevent_hit(hit) or not self.roll_accuracy(hit):
            return self.fail(hit)
        return self.do_hit(hit)

    def roll_accuracy(self, hit):
        accuracy = Effect.modify_accuracy(hit, hit.accuracy)
        if accuracy is None:
            return True
        else:
            return self.field.flip_coin(accuracy, 'Determine hit')

    def do_hit(self, hit):
        Effect.move_hit(hit)
        return self.hit(hit)

    def hit(self, hit):
        if self.power:
            self.do_damage(hit)
        return hit

    def do_damage(self, hit):
        hit.damage = self.calculate_damage(hit)
        hit.damage = Effect.modify_move_damage(self, hit.damage, hit)
        hit.target.battler.do_damage(hit.damage, direct=True)
        Effect.damage_done(hit.target, hit.damage)

    def calculate_damage(self, hit):
        # This is too mechanic-specific to have in MoveEffect
        return self.field.calculate_damage(hit)

    def deduct_pp(self):
        if self.ppless not in self.flags:
            delta = -min(self.move.pp, Effect.pp_reduction(self, 1))
            self.move.pp += delta
            self.field.message.PPChange(move=self.move, battler=self.user,
                    delta=delta, pp=self.move.pp, cause=self)

    def message_values(self, public=False):
        return dict(
                id=id(self),
                name=self.move.name,
                move=self.move.message_values(public),
                user=self.user.message_values(public),
                target=public and self.target.message_values(public),
            )

class Hit(object):
    def __init__(self, move_effect, target, **kwargs):
        self.move_effect = move_effect
        self.target = target
        self.field = move_effect.field
        self.user = move_effect.user
        self.power = move_effect.power
        self.type = move_effect.type
        self.accuracy = move_effect.accuracy
        self.damage_class = move_effect.damage_class
        self.args = kwargs
