#! /usr/bin/env python
# Encoding: UTF-8

import itertools
import random

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Trainer(object):
    """A base class for a Trainer
    """
    def __init__(self, name, team, rand=random):
        self.name = name
        self.team = team
        self.rand = rand

    def request_command(self, request):
        """Process CommandRequest: either return a Command or select() one later

        The base class implementation is geared towards simple AI trainers,
        which should implement getCommand.
        Human-played trainers should reimplement requestCommand itself.
        """
        chain = itertools.chain(self.get_commands(request), request.commands())
        for command in chain:
            if command.allowed:
                if command.command == 'move' and not command.target:
                    possible_targets = command.possible_targets
                    if len(possible_targets) == 0:
                        target = None
                    elif len(possible_targets) == 1:
                        target = possible_targets[0]
                    else:
                        target = self.choose_target(command)
                    command.target = target
                return command
        raise AssertionError("No commands available!")

    def get_commands(self, request):
        """Yield commands in order of preference.

        The first allowed one is used by requestCommand.
        If none are allowed, requestCommand will select the first one
        from the request's list.
        The base class implementation does nothing.
        """
        return ()

    def get_first_inactive_monster(self, exclude):
        """Return the first conscious team member that is not in exclude.

        The returned value is added to exclude, so that it is not selected
        again this turn.
        """
        for monster in self.team:
            if not monster.fainted and monster not in exclude:
                exclude.append(monster)
                return monster

    def get_random_inactive_monster(self, exclude):
        """Return a random conscious team member that is not in exclude.

        The returned value is added to exclude, so that it is not selected
        again this turn.
        """
        monsters = list(self.team)
        self.rand.shuffle(monsters)
        for monster in monsters:
            if not monster.fainted and monster not in exclude:
                exclude.append(monster)
                return monster

    def choose_target(self, command):
        """Choose a target for a command. Similar to requestCommand.
        """
        for target in itertools.chain(
                self.get_targets(command),
                command.possibleTargets,
            ):
            return target

    def get_targets(self, command):
        """Yield targets in order of preference. Similar to getCommands.
        """
        return ()
