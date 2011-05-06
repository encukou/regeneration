#! /usr/bin/env python
# Encoding: UTF-8

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Arg(object):
    def __init__(self, name):
        self.name = name

side = Arg('side')
battler = Arg('battler')
turn = Arg('turn')

class Message(object):
    args = ()
    def __init__(self, field, **kwargs):
        self.field = field
        for cls in type(self).mro():
            try:
                args = list(cls.args)
            except TypeError:
                args = [cls.args]
            except AttributeError:
                continue
            for arg in args:
                setattr(self, arg.name, kwargs.pop(arg.name))

class BattleStart(Message):
    "The battle is starting"
    shown = False
class BattleEnd(Message):
    pass
class Victory(BattleEnd):
    "{side} won!"
    args = side
class Draw(BattleEnd):
    "It's a draw!"
    side = None
class SendOut(Message):
    "{battler.trainer.name} sends out {battler}"
    args = battler
class TurnStart(Message):
    "Turn {turn} starts."
    args = turn
    shown = False
class TurnEnd(Message):
    "Turn {turn} ends."
    args = turn
    shown = False
class SubturnStart(Message):
    "{battler}'s subturn {turn} starts."
    args = turn, battler
    shown = None
class SubturnEnd(Message):
    "{battler}'s subturn {turn} ends."
    args = turn, battler
    shown = None
