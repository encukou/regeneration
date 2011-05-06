#! /usr/bin/python
# Encoding: UTF-8

from regeneration.battle.example import loader
from regeneration.battle.test import QuietTestCase, FakeRand

from regeneration.battle import field
from regeneration.battle import trainer
from regeneration.battle import monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Object(object):
    pass

fake_rand = FakeRand()

class TestField(QuietTestCase):
    def setup_method(self, m):
        super(TestField, self).setup_method(m)

        red = trainer.Trainer(
                'red',
                [self.make_monster() for i in range(2)],
                rand = fake_rand,
            )

        blue = trainer.Trainer(
                'blue',
                [self.make_monster() for i in range(2)],
                rand = fake_rand,
            )

        self.field = field.Field(loader, [[red], [blue]], rand=fake_rand)

    def make_monster(self):
        return monster.Monster(
                form=loader.load_form(u'porygon'),
                level=50,
                loader=loader,
                rand=fake_rand,
            )

    def test_field(self):
        self.field.run()
