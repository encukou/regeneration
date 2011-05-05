#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import raises

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import assert_equal, QuietTestCase, FakeRand

from regeneration.battle import trainer
from regeneration.battle import command

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Object(object):
    pass

class TestTrainer(QuietTestCase):
    def setUp(self):
        super(TestTrainer, self).setUp()

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
        self.request.battler = Object()
        self.request.field = Object()
        self.request.field.battlers = [self.request.battler]
        self.request.field.command_allowed = lambda command: True

    def check_move_result(self, result, command='move', target='c'):
        assert_equal(result.command, command)
        assert_equal(result.move, self.move)
        assert_equal(result.target, target)

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

    @raises(AssertionError)
    def test_no_command(self):
        self.request.commands = lambda: []
        result = self.trainer.request_command(self.request)

    def test_first_inactive(self):
        assert_equal(self.trainer.get_first_inactive_monster([]), self.mon1)
        assert_equal(
                self.trainer.get_first_inactive_monster([self.mon1]),
                self.mon2,
            )
        assert_equal(
                self.trainer.get_first_inactive_monster([self.mon1, self.mon2]),
                None,
            )

    def test_exclusion_inactive(self):
        exclude = []
        assert_equal(self.trainer.get_first_inactive_monster(exclude), self.mon1)
        assert_equal(self.trainer.get_first_inactive_monster(exclude), self.mon2)
        assert_equal(self.trainer.get_first_inactive_monster(exclude), None)

    def test_random_inactive(self):
        assert_equal(self.trainer.get_random_inactive_monster([]), self.mon2)
        assert_equal(
                self.trainer.get_random_inactive_monster([self.mon1]),
                self.mon2,
            )
        assert_equal(
                self.trainer.get_random_inactive_monster([self.mon1, self.mon2]),
                None,
            )

    def test_exclusion_random(self):
        exclude = []
        assert_equal(self.trainer.get_random_inactive_monster(exclude), self.mon2)
        assert_equal(self.trainer.get_random_inactive_monster(exclude), self.mon1)
        assert_equal(self.trainer.get_random_inactive_monster(exclude), None)
