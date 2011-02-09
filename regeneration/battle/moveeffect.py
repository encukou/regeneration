#! /usr/bin/python
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
        self.damageClass = move.damageClass
        self.targetting = move.targetting

    @classmethod
    def beginTurn(cls, field, user, target):
        """Called at the beginning of a turn, before instantiation"""
        return None

    def copyToUser(self, user):
        return type(self)(self.field, self.move, user, self.target)

    def fail(self, hit=None):
        """Signals failure"""
        return

    def attemptUse(self, **kwargs):
        if Effect.preventUse(self):
            return self.fail()
        return self.doUse()

    def doUse(self, **kwargs):
        self.deductPP()
        return self.use(**kwargs)

    def use(self, **kwargs):
        self.hits = [hit for hit in self.hits(**kwargs)]
        return [self.attemptHit(hit) for hit in self.hits]

    def hits(self, **kwargs):
        hits = []
        for target in self.getTargets(**kwargs):
            if self.targettable(target, **kwargs):
                hits.append(Hit(self, target, **kwargs))
        return hits

    def getTargets(self, **kwargs):
        return self.targetting.getTargets(self.user, self.target)

    def targettable(self, target, **kwargs):
        return not target.fainted

    def attemptHit(self, hit):
        if Effect.preventHit(hit) or not self.rollAccuracy(hit):
            return self.fail(hit)
        return self.doHit(hit)

    def rollAccuracy(self, hit):
        accuracy = Effect.modifyAccuracy(hit, hit.accuracy)
        if accuracy is None:
            return True
        else:
            return self.field.flipCoin(accuracy, 'Determine hit')

    def doHit(self, hit):
        Effect.moveHit(hit)
        return self.hit(hit)

    def hit(self, hit):
        if self.power:
            self.doDamage(hit)
        return hit

    def doDamage(self, hit):
        hit.damage = self.calculateDamage(hit)
        hit.damage = Effect.modifyMoveDamage(self, hit.damage, hit)
        hit.target.hp -= hit.damage
        Effect.moveDamageDone(hit)
        Effect.damageDone(hit.target, hit.damage)

    def calculateDamage(self, hit):
        # This is too mechanic-specific to have in MoveEffect
        return self.field.calculateMoveDamage(hit)

    def deductPP(self):
        if self.ppless not in self.flags:
            self.move.pp -= Effect.ppReduction(self, 1)

class Hit(object):
    def __init__(self, moveEffect, target, **kwargs):
        self.moveEffect = moveEffect
        self.target = target
        self.field = moveEffect.field
        self.user = moveEffect.user
        self.power = moveEffect.power
        self.type = moveEffect.type
        self.accuracy = moveEffect.accuracy
        self.damageClass = moveEffect.damageClass
        self.args = kwargs
