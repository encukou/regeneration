#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_equal, assert_almost_equal

from regeneration.battle.test import quiet
from regeneration.battle.example import connect, tables, loader

from regeneration.battle import battler, monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class FakeRand(object):
    def randint(self, a, b):
        return 0

    def choice(self, lst):
        return lst[0]

@quiet
def testBattler():
    session = connect()

    species = session.query(tables.Form).filter_by(id=1).one()
    bulba = monster.Monster(species, 30, loader.natures, rand=FakeRand())
    bulba = battler.Battler(bulba, None)

    assert_equal(bulba.ability.id, 65)
    bulba.ability = loader.loadAbility(1)
    assert_equal(bulba.ability.id, 1)
    assert_equal(bulba.monster.ability.id, 65)

    assert_equal(bulba.gender.identifier, 'female')
    assert_equal(
            [m.kind.identifier for m in bulba.moves],
            'double-edge growth sweet-scent razor-leaf'.split(),
        )
    bulba.setMove(0, loader.loadMove(1))
    assert_equal(
            [m.kind.identifier for m in bulba.moves],
            'pound growth sweet-scent razor-leaf'.split(),
        )
    assert_equal(
            [m.kind.identifier for m in bulba.monster.moves],
            'double-edge growth sweet-scent razor-leaf'.split(),
        )

    assert_equal(bulba.tameness, 70)
    assert bulba.name.endswith('saur')

    assert not bulba.fainted
    bulba.hp = 0
    assert bulba.fainted
    assert bulba.monster.fainted

    assert bulba.status == monster.Status.ok
    bulba.status = monster.Status.par
    assert bulba.status == monster.Status.par
    assert bulba.monster.status == monster.Status.par

    assert_equal(bulba.item, None)
    bulba.item = loader.loadItem(30)
    assert_equal(bulba.item.id, 30)
    assert_equal(bulba.monster.item.id, 30)

    assert_equal(bulba.level, 30)
    bulba.level = 10
    assert_equal(bulba.level, 10)
    assert_equal(bulba.monster.level, 30)
