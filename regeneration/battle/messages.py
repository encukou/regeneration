#! /usr/bin/env python
# Encoding: UTF-8

from multimethod import multimethod
from collections import Mapping

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@multimethod(object, object)
def message_values(obj, trainer):
    return obj.message_values(trainer)

for type_ in (int, unicode, bool, type(None)):
    @multimethod(type_, object)
    def message_values(scalar, trainer):
        return scalar

class MessageArgument(object):
    pass


message_registry = {}

class MessageMeta(Mapping.__metaclass__):
    def __new__(meta, classname, bases, attrs):
        argument_types = dict()
        for base in bases:
            if isinstance(base, MessageMeta):
                argument_types.update(base.argument_types)
        for name, value in list(attrs.items()):
            if isinstance(value, MessageArgument):
                value.name = name
                argument_types[name] = value
                del attrs[name]
        cls = super(MessageMeta, meta).__new__(meta, classname, bases, attrs)
        try:
            registry_name = attrs['registry_name']
        except KeyError:
            cls.registry_name = registry_name = classname
        if registry_name in message_registry:
            raise ValueError(
                    "%s already registered to %s, can't replace with %s" % (
                        registry_name,
                        message_registry[registry_name],
                        cls,
                    )
                )
        message_registry[registry_name] = cls
        cls.argument_types = argument_types
        return cls

class Message(Mapping):
    shown = True
    field = MessageArgument()
    __metaclass__ = MessageMeta

    def __init__(self, field, **kwargs):
        self.arguments = dict()
        _contents = kwargs.get('_contents')
        if _contents:
            self._contents = _contents
            return
        self._contents = dict()
        kwargs['field'] = field
        for name in self.argument_types:
            self.arguments[name] = kwargs.pop(name)
        if kwargs:
            raise ValueError("Extra keyword arguments: %s" % ', '.join(kwargs))

    def contents(self, trainer=None, save=True):
        try:
            return self._contents[trainer]
        except KeyError:
            contents = dict()
            contents['class'] = self.registry_name
            for name, arg_type in self.argument_types.items():
                value = self.arguments[name]
                contents[name] = message_values(value, trainer)
            if save:
                self._contents[trainer] = contents
            return contents

    def __getattr__(self, attr):
        return getattr(_ValueProxy(self.contents()), attr)

    def __getitem__(self, item):
        return getattr(_ValueProxy(self.contents()), item)

    def __iter__(self):
        return iter(self.argument_types)

    def __len__(self):
        return len(self.argument_types)

    def __unicode__(self):
        return unicode(self.message).format(**dict(self))

    def __str__(self):
        return unicode(self).encode('utf-8')

class _ValueProxy(object):
    def __init__(self, dct):
        self.dict = dct

    def __getattr__(self, attr):
        try:
            value = self.dict[attr]
        except KeyError:
            raise AttributeError(attr)
        if isinstance(value, dict):
            return _ValueProxy(value)
        else:
            return value

    def __repr__(self):
        return "<%s>" % self.dict

    def __unicode__(self):
        return self.dict.get('name', '<?>')


class BattleStart(Message):
    message = "The battle is starting"
    shown = False

class BattleEnd(Message):
    side = MessageArgument()

class Victory(BattleEnd):
    message = "Side {side} won!"

class Draw(BattleEnd):
    message = "It's a draw!"
    def __init__(self, field):
        super(Draw, self).__init__(field, side=None)

class SendOut(Message):
    message = "{battler.spot.trainer} sent out {battler}"
    battler = MessageArgument()

class Withdraw(Message):
    message = "{battler.spot.trainer} withdrew {battler}"
    battler = MessageArgument()

class TurnStart(Message):
    message = "Turn {turn} starts."
    shown = False
    turn = MessageArgument()

class TurnEnd(Message):
    message = "Turn {turn} ends."
    shown = False
    turn = MessageArgument()

class SubturnStart(Message):
    message = "{battler}'s subturn {turn} starts."
    shown = None
    turn = MessageArgument()
    battler = MessageArgument()

class SubturnEnd(Message):
    message = "{battler}'s subturn {turn} ends."
    shown = None
    turn = MessageArgument()
    battler = MessageArgument()


class UseMove(Message):
    message = "{battler} used {moveeffect.move}!"
    moveeffect = MessageArgument()
    battler = MessageArgument()

class HPChange(Message):
    message = "{battler} is down to {hp} HP!"
    battler = MessageArgument()
    delta = MessageArgument()
    hp = MessageArgument()
    direct = MessageArgument()

class PPChange(Message):
    message = "{battler}'s {move} is down to {pp} PP!"
    battler = MessageArgument()
    move = MessageArgument()
    delta = MessageArgument()
    pp = MessageArgument()
    cause = MessageArgument()

class Fainted(Message):
    message = "{battler} fainted!"
    battler = MessageArgument()


class EffectivityBase(Message):
    hit = MessageArgument()

class DidntAffect(EffectivityBase):
    message = "It didn't affect {hit.target}."

class NotVeryEffective(EffectivityBase):
    message = "It's not very effective!"

class NormallyEffective(EffectivityBase):
    message = "It's normally effective!"
    shown = False

class SuperEffective(EffectivityBase):
    message = "It's super effective!"

def effectivity(hit, **kwargs):
    if hit.effectivity == 0:
        return DidntAffect(hit=hit, **kwargs)
    elif hit.effectivity < 1:
        return NotVeryEffective(hit=hit, **kwargs)
    elif hit.effectivity == 1:
        return NormallyEffective(hit=hit, **kwargs)
    else:
        return SuperEffective(hit=hit, **kwargs)

class Miss(Message):
    message = "{hit.moveeffect.user}'s attack missed."
    hit = MessageArgument()

class Failed(Message):
    message = "But, it failed."
    moveeffect = MessageArgument()

class CriticalHit(Message):
    message = "A critical hit!"
    hit = MessageArgument()


class StatChange(Message):
    battler = MessageArgument()
    stat = MessageArgument()
    delta = MessageArgument()
    direction = MessageArgument()

    def __init__(self, field, **kwargs):
        super(StatChange, self).__init__(field, **kwargs)
        delta = kwargs['delta']
        direction = kwargs['direction']
        if delta <= -2:
            self.message = "{battler}'s {stat} harshly fell!"
        elif delta == -1:
            self.message = "{battler}'s {stat} fell!"
        elif delta == 0 and direction < 0:
            self.message = "{battler}'s {stat} won't go lower!"
        elif delta == 0 and direction > 0:
            self.message = "{battler}'s {stat} won't go higher!"
        elif delta == 1:
            self.message = "{battler}'s {stat} rose!"
        elif delta >= 2:
            self.message = "{battler}'s {stat} sharply rose!"


class GainAbility(Message):
    battler = MessageArgument()
    ability = MessageArgument()

class NoTarget(Message):
    message = "But, there was no opponent!"
    moveeffect = MessageArgument()
