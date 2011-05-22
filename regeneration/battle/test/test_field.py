#! /usr/bin/env python
# Encoding: UTF-8

from regeneration.battle.example import loader
from regeneration.battle.test import QuietTestCase, FakeRand

from regeneration.battle.field import Field
from regeneration.battle.trainer import Trainer
from regeneration.battle.monster import Monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Object(object):
    pass

fake_rand = FakeRand()

class TestField(QuietTestCase):

    def make_monster(self):
        return Monster(
                form=loader.load_form(u'porygon'),
                level=50,
                loader=loader,
                rand=fake_rand,
            )

    def test_field(self):
        red = Trainer(
                'red',
                [self.make_monster() for i in range(2)],
                rand = fake_rand,
            )

        blue = Trainer(
                'blue',
                [self.make_monster() for i in range(2)],
                rand = fake_rand,
            )

        field = Field(loader, [[red], [blue]], rand=fake_rand)
        field.run()
