#! /usr/bin/python
# Encoding: UTF-8

from regeneration.battle.test import FakeRand, quiet
from regeneration.battle.gender import Gender
from regeneration.battle.example import connect, tables, loader, FormTable

from regeneration.battle import monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def test_monster():
    session = connect()

    species = session.query(FormTable).filter_by(id=1).one()
    bulba = monster.Monster(species, 30, loader, rand=FakeRand())
    assert bulba.ability.identifier == 'overgrow'
    assert bulba.gender.identifier == 'female'
    assert (
            [m.kind.identifier for m in bulba.moves] ==
            'double-edge growth sweet-scent razor-leaf'.split()
        )
    assert bulba.tameness == 70
    assert not bulba.fainted
    assert bulba.name.endswith('saur')
    bulba.name = 'Testcase exhibit A'
    assert bulba.name == 'Testcase exhibit A'
    assert str(bulba) == bulba.name
    assert repr(bulba) == '<Monster %s>' % bulba.name
    bulba.name = None
    assert bulba.name.endswith('saur')

    def roundtrip(mon):
        saved = mon.save()
        loaded = monster.Monster.load(saved, loader)
        resaved = loaded.save()
        assert saved == resaved
    roundtrip(bulba)

    bulba.shiny = False
    bulba.effort.hp = 100
    bulba.genes.defense = 3
    bulba.name = 'Testcase exhibit B'
    bulba.item = loader.load_item('fresh-water')
    bulba.gender = Gender.male
    bulba.nature = loader.natures[1]
    bulba.ability = loader.load_ability('own-tempo')
    bulba.tameness = 0
    bulba.hp = 0
    bulba.status = 'par'
    bulba.set_moves([loader.load_move('petal-dance'), loader.load_move('bind')])
    bulba.set_move(0, loader.load_move('pound'))
    assert [move.kind.identifier for move in bulba.moves] == ['pound', 'bind']
    assert bulba.fainted
    bulba.recalculate_stats()

    roundtrip(bulba)

    bulba.hp = 2
    bulba.effort.hp = 0
    bulba.level = 5
    bulba.recalculate_stats()
    assert bulba.hp == 0

    saved = bulba.save()
    del saved['genes']
    assert monster.Monster.load(saved, loader).genes.values() == [0] * 6

    species = session.query(FormTable).filter_by(id=137).one()
    gon = monster.Monster(species, 30, loader, rand=FakeRand())
    assert gon.ability.identifier == 'trace'
    assert gon.gender.identifier == 'none'

@quiet
def test_loader():
    assert loader.load_form('hypno').species.identifier == 'hypno'
    assert loader.load_move('gust').identifier == 'gust'
    assert loader.load_nature('brave').identifier == 'brave'
    assert loader.load_ability('minus').identifier == 'minus'
    assert loader.load_item('stick').identifier == 'stick'
