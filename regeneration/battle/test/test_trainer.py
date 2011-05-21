#! /usr/bin/env python
# Encoding: UTF-8

import pytest

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import QuietTestCase, FakeRand

from regeneration.battle import trainer
from regeneration.battle import command

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Object(object):
    pass

class TestTrainer(QuietTestCase):
    def setup_method(self, m):
        super(TestTrainer, self).setup_method(m)

        self.mon1 = Object()
        self.mon1.fainted = False
        self.mon1.name = 'mon1'
        self.mon2 = Object()
        self.mon2.fainted = False
        self.mon2.name = 'mon2'
        self.trainer = trainer.Trainer(
                'Blue',
                [self.mon1, self.mon2],
                FakeRand(),
            )

        self.move = Object()
        self.move.targetting = Object()
        self.move.targetting.choice_list = lambda u, b: ['c', 'd']

        self.request = Object()
        self.request.commands = lambda: [
                command.MoveCommand(self.request, self.move),
            ]
        self.request.moves = lambda: self.request.commands()
        self.request.battler = Object()
        self.request.field = Object()
        self.request.field.battlers = [self.request.battler]
        self.request.field.command_allowed = lambda command: True

    def check_move_result(self, result, command='move', target='c'):
        assert result.command == command
        assert result.move == self.move
        assert result.target == target

    def test_trainer(self):
        result = self.trainer.request_command(self.request)
        self.check_move_result(result, target=None)

    def test_one_target(self):
        self.move.targetting.choice_list = lambda u, b: ['e']
        result = self.trainer.request_command(self.request)
        self.check_move_result(result, target='e')

    def test_no_target(self):
        self.move.targetting.choice_list = lambda u, b: []
        result = self.trainer.request_command(self.request)
        self.check_move_result(result, target=None)

    def test_no_command(self):
        with pytest.raises(Exception):
            self.request.commands = lambda: []
            result = self.trainer.request_command(self.request)

    def test_first_inactive(self):
        assert self.trainer.get_first_inactive_monster([]) == self.mon1
        assert (
                self.trainer.get_first_inactive_monster([self.mon1]) ==
                self.mon2
            )
        assert (
                None ==
                self.trainer.get_first_inactive_monster([self.mon1, self.mon2])
            )

    def test_exclusion_inactive(self):
        exclude = []
        assert self.trainer.get_first_inactive_monster(exclude) == self.mon1
        assert self.trainer.get_first_inactive_monster(exclude) == self.mon2
        assert self.trainer.get_first_inactive_monster(exclude) == None

    def test_random_inactive(self):
        assert self.trainer.get_random_inactive_monster([]) == self.mon2
        assert (
                self.trainer.get_random_inactive_monster([self.mon1]) ==
                self.mon2
            )
        assert (
                None ==
                self.trainer.get_random_inactive_monster([self.mon1, self.mon2])
            )

    def test_exclusion_random(self):
        exclude = []
        assert self.trainer.get_random_inactive_monster(exclude) == self.mon2
        assert self.trainer.get_random_inactive_monster(exclude) == self.mon1
        assert self.trainer.get_random_inactive_monster(exclude) == None
