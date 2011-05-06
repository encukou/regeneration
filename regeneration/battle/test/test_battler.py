#! /usr/bin/env python
# Encoding: UTF-8

from regeneration.battle.test import quiet
from regeneration.battle.example import connect, tables, loader, FormTable

from regeneration.battle import battler, monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class FakeRand(object):
    def randint(self, a, b):
        return 0

    def choice(self, lst):
        return lst[0]

class FakeSpot(object):
    field = None

@quiet
def test_battler():
    session = connect()

    species = session.query(FormTable).filter_by(id=1).one()
    bulba = monster.Monster(species, 30, loader, rand=FakeRand())
    bulba = battler.Battler(bulba, FakeSpot(), loader)

    assert bulba.ability.id == 65
    bulba.ability = loader.load_ability('stench')
    assert bulba.ability.id == 1
    assert bulba.monster.ability.id == 65

    assert bulba.gender.identifier == 'female'
    assert (
            [m.kind.identifier for m in bulba.moves] ==
            'double-edge growth sweet-scent razor-leaf'.split()
        )
    bulba.set_move(0, loader.load_move('pound'))
    assert (
            [m.kind.identifier for m in bulba.moves] ==
            'pound growth sweet-scent razor-leaf'.split()
        )
    assert (
            [m.kind.identifier for m in bulba.monster.moves] ==
            'double-edge growth sweet-scent razor-leaf'.split()
        )

    assert bulba.tameness == 70
    assert bulba.name.endswith('saur')

    assert not bulba.fainted
    bulba.hp = 0
    assert bulba.fainted
    assert bulba.monster.fainted

    assert bulba.status == 'ok'
    bulba.status = 'par'
    assert bulba.status == 'par'
    assert bulba.monster.status == 'par'

    assert bulba.item == None
    bulba.item = loader.load_item('fresh-water')
    assert bulba.item.id == 30
    assert bulba.monster.item.id == 30

    assert bulba.level == 30
    bulba.level = 10
    assert bulba.level == 10
    assert bulba.monster.level == 30
