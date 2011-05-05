#! /usr/bin/python
# Encoding: UTF-8

from itertools import chain, izip_longest, product

from nose.tools import assert_equal

from regeneration.battle.example import connect, tables, loader, FormTable
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
        self.selected_commands = []

    def command_allowed(self, command):
        return True

    def command_selected(self, command):
        self.selected_commands.append(command)

    struggle = loader.load_struggle()
    battlers = ['none']

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
        cls.species = cls.session.query(FormTable).filter_by(id=1).one()

    def setUp(self):
        super(TestCommand, self).setUp()
        self.bulba = monster.Monster(self.species, 30, loader, rand=FakeRand())
        self.battler = battler.Battler(self.bulba, FakeSpot(), loader)
        self.battler.spot.battler = self.battler

        self.request = command.CommandRequest(self.battler.spot)

    @quiet
    def test_move_commands(self):
        for move_command, move in izip_longest(
                self.request.moves(),
                self.battler.moves,
            ):
            assert_equal(move_command.command, 'move')
            assert_equal(move_command.battler, self.battler)
            assert_equal(move_command.move, move)
            assert_equal(move_command.target, None)

    @quiet
    def test_switch_commands(self):
        for switch_command, replacement in izip_longest(
                self.request.switches(),
                FakeTrainer.team,
            ):
            assert_equal(switch_command.command, 'switch')
            assert_equal(switch_command.battler, self.battler)
            assert_equal(switch_command.replacement, replacement)

    @quiet
    def test_item_commands(self):
        for item_command, item in izip_longest(
                self.request.items(),
                ('fake', 'item'),
            ):
            assert_equal(item_command.command, 'item')
            assert_equal(item_command.battler, self.battler)
            assert_equal(item_command.item, item)

    @quiet
    def test_forfeit_commands(self):
        for run_command, run in izip_longest(
                self.request.forfeits(),
                ['run'],
            ):
            assert_equal(run_command.command, 'run')
            assert_equal(run_command.battler, self.battler)

    @quiet
    def test_all_commands(self):
        for command_a, command_b in izip_longest(
                chain(
                        self.request.moves(),
                        self.request.switches(),
                        self.request.items(),
                        self.request.forfeits(),
                    ),
                self.request.commands(),
            ):
            assert_equal(command_a, command_b)

    @quiet
    def test_unallowed_commands(self):
        self.request.field.command_allowed = lambda self: False

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
    def test_targets(self):
        for cmd in self.request.commands():
            cmd.select()
        assert_equal(
                list(self.request.commands()),
                list(self.request.field.selected_commands),
            )

    @quiet
    def test_equalities(self):
        for (i1, cmd1), (i2, cmd2) in product(
                *[enumerate(self.request.commands()) for i in range(2)]
            ):
            if i1 == i2:
                assert cmd1 == cmd2
            else:
                assert cmd1 != cmd2

    @quiet
    def test_no_items(self):
        local_battler = battler.Battler(self.bulba, FakeSpot(), loader)
        local_request = command.CommandRequest(local_battler)
        del local_battler.spot.trainer.items

        assert_equal(list(self.request.items()), [])
