#! /usr/bin/env python
# Encoding: UTF-8

from itertools import chain, izip_longest, product

from regeneration.battle.example import connect, tables, loader, FormTable
from regeneration.battle.test import quiet, FakeRand, QuietTestCase

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
    def __init__(self):
        self.field = FakeField()
        self.trainer = FakeTrainer()

class TestCommand(QuietTestCase):
    @classmethod
    def setup_class(cls):
        cls.session = connect()
        cls.species = cls.session.query(FormTable).filter_by(id=1).one()

    def setup_method(self, m):
        super(TestCommand, self).setup_method(m)
        self.bulba = monster.Monster(self.species, 30, loader, rand=FakeRand())
        self.battler = battler.Battler(self.bulba, FakeSpot(), loader)
        self.battler.spot.battler = self.battler

        self.request = command.CommandRequest(self.battler)

    @quiet
    def test_move_commands(self):
        for move_command, move in izip_longest(
                self.request.moves(),
                self.battler.moves,
            ):
            assert move_command.command, 'move'
            assert move_command.battler == self.battler
            assert move_command.move == move
            assert move_command.target == None

    @quiet
    def test_switch_commands(self):
        for switch_command, replacement in izip_longest(
                self.request.switches(),
                FakeTrainer.team,
            ):
            assert switch_command.command == 'switch'
            assert switch_command.battler == self.battler
            assert switch_command.replacement == replacement

    @quiet
    def test_item_commands(self):
        for item_command, item in izip_longest(
                self.request.items(),
                ('fake', 'item'),
            ):
            assert item_command.command == 'item'
            assert item_command.battler == self.battler
            assert item_command.item == item

    @quiet
    def test_forfeit_commands(self):
        for run_command, run in izip_longest(
                self.request.forfeits(),
                ['run'],
            ):
            assert run_command.command == 'run'
            assert run_command.battler == self.battler

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
            assert command_a == command_b

    @quiet
    def test_unallowed_commands(self):
        self.request.field.command_allowed = lambda self: False

        (struggle, ) = self.request.moves()
        assert struggle.command == 'move'
        assert struggle.move.kind == FakeField.struggle

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
        assert (
                list(self.request.commands()) ==
                list(self.request.field.selected_commands)
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

        assert list(local_request.items()) == []
