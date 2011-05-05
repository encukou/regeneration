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
        self.move.targetting.chooseList = lambda u, b: ['c', 'd']

        self.request = Object()
        self.request.commands = lambda: [
                command.MoveCommand(self.request, self.move),
            ]
        self.request.battler = Object()
        self.request.field = Object()
        self.request.field.battlers = [self.request.battler]
        self.request.field.commandAllowed = lambda command: True

    def checkMoveResult(self, result, command='move', target='c'):
        assert_equal(result.command, command)
        assert_equal(result.move, self.move)
        assert_equal(result.target, target)

    def testTrainer(self):
        result = self.trainer.requestCommand(self.request)
        self.checkMoveResult(result)

    def testOneTarget(self):
        self.move.targetting.chooseList = lambda u, b: ['e']
        result = self.trainer.requestCommand(self.request)
        self.checkMoveResult(result, target='e')

    def testNoTarget(self):
        self.move.targetting.chooseList = lambda u, b: []
        result = self.trainer.requestCommand(self.request)
        self.checkMoveResult(result, target=None)

    @raises(AssertionError)
    def testNoCommand(self):
        self.request.commands = lambda: []
        result = self.trainer.requestCommand(self.request)

    def testFirstInactive(self):
        assert_equal(self.trainer.getFirstInactiveMonster([]), self.mon1)
        assert_equal(
                self.trainer.getFirstInactiveMonster([self.mon1]),
                self.mon2,
            )
        assert_equal(
                self.trainer.getFirstInactiveMonster([self.mon1, self.mon2]),
                None,
            )

    def testExclusionInactive(self):
        exclude = []
        assert_equal(self.trainer.getFirstInactiveMonster(exclude), self.mon1)
        assert_equal(self.trainer.getFirstInactiveMonster(exclude), self.mon2)
        assert_equal(self.trainer.getFirstInactiveMonster(exclude), None)

    def testRandomInactive(self):
        assert_equal(self.trainer.getRandomInactiveMonster([]), self.mon2)
        assert_equal(
                self.trainer.getRandomInactiveMonster([self.mon1]),
                self.mon2,
            )
        assert_equal(
                self.trainer.getRandomInactiveMonster([self.mon1, self.mon2]),
                None,
            )

    def testExclusionRandom(self):
        exclude = []
        assert_equal(self.trainer.getRandomInactiveMonster(exclude), self.mon2)
        assert_equal(self.trainer.getRandomInactiveMonster(exclude), self.mon1)
        assert_equal(self.trainer.getRandomInactiveMonster(exclude), None)