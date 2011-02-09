#! /usr/bin/python
# Encoding: UTF-8

from contextlib import contextmanager
from functools import wraps, partial

from regeneration.battle.enum import Enum

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class EffectSubject(object):
    """Something that can have Effects on it, e.g. Field, Side, Battler
    """
    def __init__(self, field):
        self.effects = []
        self.field = field

    activeSubSubjects = ()

    def applyEffect(self, effect, inducer):
        """Apply an Effect to this subject.

        Returns the effect, or None on failure
        """
        if not effect:
            return None
        effect.subject = self
        effect.field = self.field
        effect.inducer = inducer
        effect.active = True
        uniqueClass = effect.uniqueClass
        if uniqueClass and self.getEffect(uniqueClass):
            return None
        if effect.blockApplication(effect):
            return None
        if Effect.blockApplication(effect):
            return None
        self.effects.append(effect)
        for e in self.field.activeEffects:
            e.effectApplied(effect)
        return effect

    def giveEffect(self, target, effect):
        """Apply an effect to a given target, with this as the inducer
        """
        return target.applyEffect(effect, inducer=self)

    def giveEffectSelf(self, effect):
        """Apply an effect to this subject, making it the inducer also
        """
        return self.applyEffect(effect, inducer=self)

    def getEffects(self, effectClass=None):
        """Yield all effects of the given class.

        effectClass may be a base class or a tuple of classes, as with
        isinstance().
        """
        if effectClass is None:
            effectClass = object
        for effect in self.effects:
            if isinstance(effect, effectClass) and effect.active:
                yield effect

    def getEffect(self, effectClass=None):
        """Get an effect of the given class.

        If there are multiple effects, return the first one; if there are none,
        return None.

        effectClass may be a base class or a tuple of classes, as with
        isinstance().
        """
        for effect in self.getEffects(effectClass):
            return effect
        else:
            return None

    @property
    def activeEffects(self):
        for effect in self.effects[:]:
            if effect.active:
                yield effect
        for subSubject in self.activeSubSubjects:
            for effect in subSubject.activeEffects:
                yield effect

    def getEffectMethods(self, cls, attr):
        """Yields an attribute for all active effects of a given class.
        """
        for effect in self.activeEffects:
            if cls is None or isinstance(effect, cls):
                yield getattr(effect, attr)

def uniqueEffect(cls):
    """Decorator for unique effects; only one instance of such a class
    is allowed on a single subject. These may be singletons (e.g. infatuation),
    or exclusive classes (like the fixed status effects).
    """
    cls.uniqueClass = cls
    return cls

def returnList(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return list(func(*args, **kwargs))
    return wrapped

class callback(object):
    """A magic callback method

    When called from an instance, behaves normally. However, when called from
    an Effect class, it is called on all active effects in the battle.
    A list containing all true return values is returned.

    The first argument must have a field attribute that gives the battlefield.
    """
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance:
            return partial(self.func, instance)
        else:
            return wraps(self.func)(partial(self.runAll, owner))

    def getEffectMethods(self, owner, object):
        return object.field.getEffectMethods(owner, self.name)

    @returnList
    def runAll(self, owner, object, *args, **kwargs):
        for method in self.getEffectMethods(owner, object):
            value = method(object, *args, **kwargs)
            if value:
                yield value

class chain(callback):
    """A yet more magic callback, which chains its second argument

    "Chain" means that the return value of one method is passed as the second
    argument to the next, and the last one is returned.
    """

    def runAll(self, owner, object, value, *args, **kwargs):
        for method in self.getEffectMethods(owner, object):
            value = method(object, value, *args, **kwargs)
        return value

class Effect(object):
    """An effect is something that interacts with moves, other effects, and
    the battle in general.

    Each effect has a subject, which is usually a Battler, but can also be
    a Side (for Spikes, for example), or the Battlefield (e.g. for weather).

    Effects are implemented using callbacks.

    Generally, *each* effect's callback is called whenever something
    interesting or overridable happens. Thus, many effect methods will start
    with something like "if subject is self.subject".

    Always apply effects using effectSubject methods (giveEffect etc.).
    """
    uniqueClass = None

    active = False

    def __init__(self):
        """Always call EffectSubject's methods to properly apply Effects!
        """

    def reparent(self, newSubject):
        """Move the effect onto another subject.
        This is only for quick hacks, and generally shouldn't be used.
        """
        self.subject.effects = [
                e for e
                in self.subject.effects
                if e is not self
            ]
        self.subject = newSubject
        self.subject.effects.append(self)

    def remove(self):
        Effect.effectRemoved(self)
        self.active = False
        self.subject.effects = [
                e for e
                in self.subject.effects
                if e is not self
            ]

    @contextmanager
    def disabled(self):
        """A `with` statement context manager to disable the effect temporarily
        """
        previous = self.active
        self.active = False
        yield
        self.active = previous

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return "<%s 0x%x>" % (self.__class__.__name__, id(self))

    # Notifications

    @callback
    def effectRemoved(self, effect):
        """Called when this effect is removed.
        """
        return

    @callback
    def effectApplied(self, effect):
        """Called when some effect has been applied.
        """
        return

    @callback
    def moveHit(self, hit):
        """Called when a move connected with a target.
        """
        return

    @callback
    def moveDamageDone(self, hit):
        """Called when a move damages a target.
        """
        return

    @callback
    def damageDone(self, subject, damage):
        """Called when damage is done to battler
        """
        return

    # Cancellers

    @callback
    def blockApplication(self, effect):
        """Called when the effect is applied; return a modified effect, or None

        None cancels the application(return the original effect if that's what
        you want to do).
        """
        return False

    @callback
    def preventUse(self, moveeffect):
        """Return true to prevent the use of a move

        This includes the "X used Y" message and PP reduction.
        """
        return False

    @callback
    def preventHit(self, hit):
        """Return true to prevent a move's hit
        """
        return False

    @callback
    def prevent_switch(self, command):
        """Return true to prevent a switch
        """
        return False

    # Chainers

    @chain
    def modifyAccuracy(self, hit, accuracy):
        """Modify a hit's accuracy
        """
        return accuracy

    @chain
    def modifyMoveDamage(self, target, damage, hit):
        """Modify a hit's damage
        """
        return damage

    @chain
    def ppReduction(self, moveeffect, pp):
        """Modify a hit's damage
        """
        return pp
