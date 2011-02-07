#! /usr/bin/python
# Encoding: UTF-8

from itertools import chain, izip_longest, product

from nose.tools import assert_equal

from regeneration.battle.example import connect, tables, loader
from regeneration.battle.test import (
        quiet, FakeRand, assert_all_equal, QuietTestCase
    )

from regeneration.battle import monster
from regeneration.battle import battler
from regeneration.battle import command

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class FakeField(object):
    def __init__(self):
        self.selectedCommands = []

    def commandAllowed(self, command):
        return True

    def commandSelected(self, command):
        self.selectedCommands.append(command)

    def possibleTargets(self, command):
        return ['none']

    struggle = loader.loadMove(165)

class FakeMonster(object):
    fainted = False

class FakeTrainer(object):
    team = FakeMonster(), FakeMonster()
    def __init__(self):
        self.items = 'fake', 'item'

class FakeSpot(object):
    field = FakeField()
    trainer = FakeTrainer()

class TestCommand(QuietTestCase):
    @classmethod
    def setupClass(cls):
        cls.session = connect()
        cls.species = cls.session.query(tables.Form).filter_by(id=1).one()

    def setUp(self):
        super(TestCommand, self).setUp()
        self.bulba = monster.Monster(self.species, 30, loader.natures, rand=FakeRand())
        self.battler = battler.Battler(self.bulba, FakeSpot())

        self.request = command.CommandRequest(self.battler)

    @quiet
    def testMoveCommands(self):
        for moveCommand, move in izip_longest(
                self.request.moves(),
                self.battler.moves,
            ):
            assert_equal(moveCommand.command, 'move')
            assert_equal(moveCommand.battler, self.battler)
            assert_equal(moveCommand.move, move)
            assert_equal(moveCommand.target, None)

    @quiet
    def testSwitchCommands(self):
        for switchCommand, replacement in izip_longest(
                self.request.switches(),
                FakeTrainer.team,
            ):
            assert_equal(switchCommand.command, 'switch')
            assert_equal(switchCommand.battler, self.battler)
            assert_equal(switchCommand.replacement, replacement)

    @quiet
    def testItemCommands(self):
        for itemCommand, item in izip_longest(
                self.request.items(),
                ('fake', 'item'),
            ):
            assert_equal(itemCommand.command, 'item')
            assert_equal(itemCommand.battler, self.battler)
            assert_equal(itemCommand.item, item)

    @quiet
    def testForfeitCommands(self):
        for runCommand, run in izip_longest(
                self.request.forfeits(),
                ['run'],
            ):
            assert_equal(runCommand.command, 'run')
            assert_equal(runCommand.battler, self.battler)

    @quiet
    def testAllCommands(self):
        for commandA, commandB in izip_longest(
                chain(
                        self.request.moves(),
                        self.request.switches(),
                        self.request.items(),
                        self.request.forfeits(),
                    ),
                self.request.commands(),
            ):
            assert_equal(commandA, commandB)

    @quiet
    def testUnallowedCommands(self):
        self.request.field.commandAllowed = lambda self: False

        (struggle, ) = self.request.moves()
        assert_equal(struggle.command, 'move')
        assert_equal(struggle.move.kind, FakeField.struggle)

        for cmd in self.request.switches():
            raise AssertionError('%s is not allowed' % cmd)

        for cmd in self.request.items():
            raise AssertionError('%s is not allowed' % cmd)

        for cmd in self.request.forfeits():
            raise AssertionError('%s is not allowed' % cmd)

        for cmd in self.request.commands():
            if cmd != struggle:
                raise AssertionError('%s is not allowed' % cmd)

    @quiet
    def testTargetOptions(self):
        for cmd in self.request.commands():
            if cmd.command == 'move':
                assert_equal(list(cmd.possibleTargets), ['none'])
            else:
                assert_equal(list(cmd.possibleTargets), [])

    @quiet
    def testTargets(self):
        for cmd in self.request.commands():
            cmd.select()
        assert_equal(
                list(self.request.commands()),
                list(self.request.field.selectedCommands),
            )

    @quiet
    def testEqualities(self):
        for (i1, cmd1), (i2, cmd2) in product(
                *[enumerate(self.request.commands()) for i in range(2)]
            ):
            if i1 == i2:
                assert cmd1 == cmd2
            else:
                assert cmd1 != cmd2

    @quiet
    def testNoItems(self):
        localBattler = battler.Battler(self.bulba, FakeSpot())
        localRequest = command.CommandRequest(localBattler)
        del localBattler.spot.trainer.items

        assert_equal(list(self.request.items()), [])
