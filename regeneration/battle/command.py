#! /usr/bin/python
# Encoding: UTF-8

import itertools

from regeneration.battle.move import Move

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'


class Command(object):
    """A battle command: specifies what a Trainer intends to do this turn.
    """
    possibleTargets = ()

    def __init__(self, request):
        self.request = request

    def select(self):
        self.field.command_selected(self)

    @property
    def field(self):
        return self.request.field

    @property
    def battler(self):
        return self.request.battler

    @property
    def allowed(self):
        return self.field.command_allowed(self)

    def __eq__(self, other):
        return self.command == other.command and self.args == other.args

    def __ne__(self, other):
        return not self == other

class MoveCommand(Command):
    command = 'move'
    def __init__(self, request, move, target=None):
        super(MoveCommand, self).__init__(request)
        self.move = move
        self.target = target

    @property
    def possible_targets(self):
        return self.move.targetting.choice_list(
                self.request.battler,
                self.field.battlers,
            )

    @property
    def args(self):
        return self.move, self.target

class SwitchCommand(Command):
    command = 'switch'
    def __init__(self, request, replacement):
        super(SwitchCommand, self).__init__(request)
        self.replacement = replacement

    @property
    def args(self):
        return self.replacement,

class ItemCommand(Command):
    command = 'item'
    def __init__(self, request, item):
        super(ItemCommand, self).__init__(request)
        self.item = item

    @property
    def args(self):
        return self.item,

class RunCommand(Command):
    command = 'run'
    def __init__(self, request):
        super(RunCommand, self).__init__(request)

    @property
    def args(self):
        return ()

def filter_allowed(func):
    def inner(self, *args, **kwargs):
        for command in func(self, *args, **kwargs):
            if command.allowed:
                yield command
    return inner

class CommandRequest(object):
    """A request for a trainer's command.

    An instance of this class gets passed to a trainer's requestCommand method.
    It defines several iterators with different kinds of commands: moves,
    switches, etc., and a commands() that includes them all. Only legal
    commands are returned.
    """
    def __init__(self, spot):
        self.spot = spot

    def moves(self, moves=None):
        if not self.battler:
            return
        if moves is None:
            moves = self.battler.moves
        have_some_moves = False
        for move in moves:
            command = MoveCommand(self, move=move)
            if command.allowed:
                have_some_moves = True
                yield command
        if have_some_moves:
            return
        # Struggle
        struggle = Move(self.field.struggle)
        yield MoveCommand(self, move=struggle)

    @filter_allowed
    def switches(self, replacements=None):
        if replacements is None:
            replacements = self.spot.trainer.team
        for replacement in replacements:
            if not replacement.fainted:
                yield SwitchCommand(self, replacement=replacement)

    @filter_allowed
    def items(self, items=None):
        if items is None:
            try:
                items = self.battler.spot.trainer.items
            except AttributeError:
                # No items...
                items = ()
        for item in items:
            yield ItemCommand(self, item=item)

    @filter_allowed
    def forfeits(self):
        yield RunCommand(self)

    @filter_allowed
    def commands(self, moves=None, replacements=None, items=None):
        for command in itertools.chain(
                self.moves(moves),
                self.switches(replacements),
                self.items(items),
                self.forfeits(),
            ):
            yield command

    @property
    def field(self):
        return self.spot.field

    @property
    def battler(self):
        return self.spot.battler
