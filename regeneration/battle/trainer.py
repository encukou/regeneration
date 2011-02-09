#! /usr/bin/python
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

    def requestCommand(self, request):
        """Process CommandRequest: either return a Command or select() one later

        The base class implementation is geared towards simple AI trainers,
        which should implement getCommand.
        Human-played trainers should reimplement requestCommand itself.
        """
        chain = itertools.chain(self.getCommands(request), request.commands())
        for command in chain:
            if command.allowed:
                if command.command == 'move' and not command.target:
                    possibleTargets = command.possibleTargets
                    if len(possibleTargets) == 0:
                        target = None
                    elif len(possibleTargets) == 1:
                        target = possibleTargets[0]
                    else:
                        target = self.chooseTarget(command)
                    command.target = target
                return command
        raise AssertionError("No commands available!")

    def getCommands(self, request):
        """Yield commands in order of preference.

        The first allowed one is used by requestCommand.
        If none are allowed, requestCommand will select the first one
        from the request's list.
        The base class implementation does nothing.
        """
        return ()

    def getFirstInactiveMonster(self, exclude):
        """Return the first conscious team member that is not in exclude.

        The returned value is added to exclude, so that it is not selected
        again this turn.
        """
        for monster in self.team:
            if not monster.fainted and monster not in exclude:
                exclude.append(monster)
                return monster

    def getRandomInactiveMonster(self, exclude):
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

    def chooseTarget(self, command):
        """Choose a target for a command. Similar to requestCommand.
        """
        for target in itertools.chain(
                self.getTargets(command),
                command.possibleTargets,
            ):
            return target

    def getTargets(self, command):
        """Yield targets in order of preference. Similar to getCommands.
        """
        return ()
