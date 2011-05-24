#! /usr/bin/env python
# Encoding: UTF-8

import itertools
import random

from regeneration.battle.monster import Monster

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Trainer(object):
    """A base class for a Trainer
    """
    MonsterClass = Monster

    def __init__(self, name, team, rand=random):
        self.name = name
        self.team = team
        self.rand = rand

    def request_command(self, request):
        """Process CommandRequest: either return a Command or select() one later

        The base class implementation is geared towards simple AI trainers,
        which should implement get_commands.
        Human-played trainers should reimplement request_command itself.
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

        The first allowed one is used by request_command.
        If none are allowed, request_command will select the first one
        from the request's list.

        Note that returning an empty tuple is perfectly fine.

        The base class implementation implements a very dumb random trainer
        that might select any command (including, on rare occasions, running)
        """
        moves = list(request.moves())
        if moves and self.rand.random() < 0.9:
            # 90% chance to just select a move
            return [self.rand.choice(moves)]
        else:
            # 10% chance to select anything (incl. another move)
            command = self.rand.choice(list(request.commands()))
            if command.command == 'run' and self.rand.random() < .99:
                # But only forfeit very rarely
                return ()
            return [command]

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
                (t for t in self.get_targets(command)
                    if t in command.possible_targets),
                command.possibleTargets,
            ):
            return target

    def get_targets(self, command):
        """Yield targets in order of preference. Similar to getCommands.
        """
        return ()

    @classmethod
    def load(cls, dct, loader, **kwargs):
        if 'seed' in dct:
            rand = random.Random(dct['seed'])
        else:
            rand = random
        monster_class = kwargs.pop('monster_class', cls.MonsterClass)
        return cls(
                name=dct['name'],
                team=[monster_class.load(d, loader) for d in dct['team']],
                rand=rand,
                **kwargs)

    def message_values(self, private=True):
        return dict(
                id=id(self),
                name=self.name,
            )
