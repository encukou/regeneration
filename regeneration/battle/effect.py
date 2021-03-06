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

    subsubjects = ()
    is_active_subject = True

    def apply_effect(self, effect, inducer,
            message_class=None, **message_args):
        """Apply an Effect to this subject.

        Returns the effect, or None on failure.

        If message_class is given, the corresponding message is sent out if
        the effect is successfully applied, before triggering other effects.
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
        if message_class:
            self.field.message(message_class, **message_args)
        Effect.effect_applied(effect)
        return effect

    def give_effect(self, target, effect, message_class=None, **message_args):
        """Apply an effect to a given target, with this as the inducer
        """
        return target.apply_effect(effect, inducer=self,
                message_class=message_class, **message_args)

    def give_effect_self(self, effect, message_class=None, **message_args):
        """Apply an effect to this subject, making it the inducer also
        """
        return self.apply_effect(effect, inducer=self,
                message_class=message_class, **message_args)

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
        for subsubject in self.subsubjects:
            for effect in subsubject.active_effects:
                if (subsubject.is_active_subject or
                        effect.active_on_fainted_subject):
                    yield effect

    def get_effect_methods(self, cls, attr, object, arguments):
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
                            yield None, effect, callback
                        else:
                            if callable(orderkey):
                                orderkey = orderkey(effect)
                                if isinstance(orderkey, collections.Iterator):
                                    for key in orderkey:
                                        yield key, effect, callback
                                    continue
                            yield orderkey, effect, callback
        return (v for k, e, v in sorted(generator())
                if e in self.active_effects and
                        not any(ef.disable_callback(e, v.__name__, arguments)
                                for ef in self.active_effects))

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

    def get_effect_methods(self, owner, object, arguments):
        return object.field.get_effect_methods(owner, self.name, object,
                arguments)

    @return_list
    def run_all(self, owner, object, *args):
        for method in self.get_effect_methods(owner, object, args):
            value = method(object, *args)
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

    def run_all(self, owner, object, value, *args):
        for method in self.get_effect_methods(owner, object, args):
            value = method(object, value, *args)
        return value

class callback_any(callback):
    """A callback that runs until the first true value, and returns it.

    If no true value is found, returns None.
    """
    def run_all(self, owner, object, *args):
        for method in self.get_effect_methods(owner, object, args):
            value = method(object, *args)
            if value:
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

    Always apply effects using effectSubject methods (give_effect etc.).

    When used as a context manager, an Effect will remove itself when exiting
    the context.
    """
    unique_class = None

    active = False
    active_on_fainted_subject = False

    def __init__(self):
        """Always call EffectSubject's methods to properly apply Effects!
        """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.remove()

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

    def disable_callback(self, effect, callback_name, arguments):
        """Return true to disable another effect's callback.
        """
        return False

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
    def move_used(self, move_effect):
        """Called when a move is used
        """

    @callback
    def move_hits_done(self, move_effect, hits):
        """Called when all of a move's hits have been executed
        """

    # Cancellers/forcers

    @callback_any
    def end_turn(self, field):
        """Called when a turn ends. Return true only if the battle should end.
        """

    @callback_any
    def block_application(self, effect):
        """Called when the effect is applied; return a modified effect, or None

        None cancels the application(return the original effect if that's what
        you want to do).
        """
        return False

    @callback_any
    def prevent_move_selection(self, command):
        """Return true to prevent the selection of a move
        """
        return False

    @callback_any
    def prevent_use(self, move_effect):
        """Return true to prevent the use of a move

        This includes the "X used Y" message and PP reduction.
        """
        return False

    @callback_any
    def prevent_hit(self, hit):
        """Return true to prevent a move's hit
        """

    @callback_any
    def prevent_switch(self, command):
        """Return true to prevent a switch
        """

    @callback_any
    def force_critical_hit(self, hit):
        """Return true to force a critical hit
        """

    @callback_any
    def prevent_critical_hit(self, hit):
        """Return true to prevent a critical hit
        """

    @callback_any
    def ensure_hit(self, hit):
        """Return true to ensure a move hits, regardless of accuracy
        """

    # Chainers

    @chain
    def modify_accuracy(self, hit, accuracy):
        """Modify a hit's accuracy
        """
        return accuracy

    @chain
    def modify_move_damage(self, hit, damage):
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
    def critical_hit_stage(self, moveeffect, stage):
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

    @chain
    def modify_effectivity(self, hit, effectivity):
        """Modify the type effectivity of a hit
        """
        return effectivity

    @chain
    def modify_secondary_chance(self, hit, chance):
        """Modify the chance for a move's secondary effect
        """
        return effectivity
