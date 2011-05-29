#! /usr/bin/env python
# Encoding: UTF-8

from contextlib import contextmanager
from functools import wraps, partial
import collections

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class EffectSubject(object):
    """Something that can have Effects on it, e.g. Field, Side, Battler
    """
    def __init__(self, field):
        self.effects = []
        self.field = field

    active_subsubjects = ()

    def apply_effect(self, effect, inducer):
        """Apply an Effect to this subject.

        Returns the effect, or None on failure
        """
        if not effect:
            return None
        effect.subject = self
        effect.field = self.field
        effect.inducer = inducer
        effect.active = True
        if getattr(effect, 'block_application', lambda e: False)(effect):
            return None
        if Effect.block_application(effect):
            return None
        self.effects.append(effect)
        Effect.effect_applied(effect)
        return effect

    def give_effect(self, target, effect):
        """Apply an effect to a given target, with this as the inducer
        """
        return target.apply_effect(effect, inducer=self)

    def give_effect_self(self, effect):
        """Apply an effect to this subject, making it the inducer also
        """
        return self.apply_effect(effect, inducer=self)

    def get_effects(self, effect_class=None):
        """Yield all effects of the given class.

        effectClass may be a base class or a tuple of classes, as with
        isinstance().
        """
        if effect_class is None:
            effect_class = object
        for effect in self.effects:
            if isinstance(effect, effect_class) and effect.active:
                yield effect

    def get_effect(self, effect_class=None):
        """Get an effect of the given class.

        If there are multiple effects, return the first one; if there are none,
        return None.

        effectClass may be a base class or a tuple of classes, as with
        isinstance().
        """
        for effect in self.get_effects(effect_class):
            return effect
        else:
            return None

    @property
    def active_effects(self):
        for effect in self.effects[:]:
            if effect.active:
                yield effect
        for subsubject in self.active_subsubjects:
            for effect in subsubject.active_effects:
                yield effect

    def get_effect_methods(self, cls, attr, object):
        """Yields an attribute for all active effects of a given class.
        """
        def generator():
            for effect in self.active_effects:
                if cls is None or isinstance(effect, cls):
                    try:
                        callback = getattr(effect, attr)
                    except AttributeError:
                        pass
                    else:
                        try:
                            orderkey = callback.orderkey
                        except AttributeError:
                            yield None, callback
                        else:
                            if callable(orderkey):
                                orderkey = orderkey(effect)
                                if isinstance(orderkey, collections.Iterator):
                                    for key in orderkey:
                                        yield key, callback
                                    continue
                            yield orderkey, callback
        return [v for k, v in sorted(generator())]

def return_list(func):
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

    Note that the decorated (base class) method itself will only be present on
    the class (not on instances), and thus will not be called. This means that
    the body of the decorated function is ignored.
    """
    def __init__(self, func, orderkey=None):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance:
            raise AttributeError(self.name)
        else:
            return wraps(self.func)(partial(self.run_all, owner))

    def get_effect_methods(self, owner, object):
        return object.field.get_effect_methods(owner, self.name, object)

    @return_list
    def run_all(self, owner, object, *args, **kwargs):
        for method in self.get_effect_methods(owner, object):
            value = method(object, *args, **kwargs)
            if value:
                yield value

class chain(callback):
    """A yet more magic callback, which chains its second argument

    "Chain" means that the return value of one method is passed as the second
    argument to the next, and the last one is returned.

    Raise StopIteration to end the chain.

    Note that the decorated (base class) method itself will only be present on
    the class (not on instances), and thus will not be called. This means that
    the body of the decorated function is ignored.
    """

    def run_all(self, owner, object, value, *args, **kwargs):
        for method in self.get_effect_methods(owner, object):
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
    unique_class = None

    active = False

    def __init__(self):
        """Always call EffectSubject's methods to properly apply Effects!
        """

    @staticmethod
    def orderkey(key):
        """Decorator to attach an order key to a callback

        A key may also be callable, in which case it's called with the
        effect as an argument.
        The callable may be a generator, in which case the callback will
        be called multiple times: once for each value.
        """
        def _attach_orderkey(func):
            func.orderkey = key
            return func
        return _attach_orderkey

    def reparent(self, new_subject):
        """Move the effect onto another subject.
        """
        self.subject.effects = [
                e for e
                in self.subject.effects
                if e is not self
            ]
        self.subject = new_subject
        self.subject.effects.append(self)

    def remove(self):
        Effect.effect_removed(self)
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
    def effect_removed(self, effect):
        """Called when an effect is removed."""

    @callback
    def effect_applied(self, effect):
        """Called when some effect has been applied."""

    @callback
    def move_hit(self, hit):
        """Called when a move connected with a target."""

    @callback
    def move_damage_done(self, hit):
        """Called when a move damages a target."""

    @callback
    def damage_done(self, subject, damage):
        """Called when damage is done to battler"""

    @callback
    def begin_turn(self, turn_number):
        """Called when a turn begins"""

    @callback
    def send_out(self, battler):
        """Called when battler is sent to battle"""

    @callback
    def withdraw(self, battler):
        """Called when battler is withdrawn from battle (incl. after fainting)
        """

    @callback
    def end_turn(self, field):
        """Called when a turn ends.
        """

    # Cancellers

    @callback
    def block_application(self, effect):
        """Called when the effect is applied; return a modified effect, or None

        None cancels the application(return the original effect if that's what
        you want to do).
        """
        return False

    @callback
    def prevent_move_selection(self, command):
        """Return true to prevent the selection of a move
        """
        return False

    @callback
    def prevent_use(self, move_effect):
        """Return true to prevent the use of a move

        This includes the "X used Y" message and PP reduction.
        """
        return False

    @callback
    def prevent_hit(self, hit):
        """Return true to prevent a move's hit
        """

    @callback
    def prevent_switch(self, command):
        """Return true to prevent a switch
        """

    # Chainers

    @chain
    def modify_accuracy(self, hit, accuracy):
        """Modify a hit's accuracy
        """
        return accuracy

    @chain
    def modify_move_damage(self, target, damage, hit):
        """Modify a hit's damage
        """
        return damage

    @chain
    def pp_reduction(self, moveeffect, pp_reduction):
        """Modify a hit's PP usage
        """
        return pp_reduction

    @chain
    def speed_factor(self, field, speed_factor):
        """Modify the global speed factor
        """
        return speed_factor

    @chain
    def critical_hit_stage(self, field, stage):
        """Modify the critical hit stage
        """
        return stage

    @chain
    def modify_stat(self, battler, value, stat):
        """Modify a stat
        """
        return value

    @chain
    def modify_base_power(self, hit, power):
        """Modify the base power of a move
        """
        return power
