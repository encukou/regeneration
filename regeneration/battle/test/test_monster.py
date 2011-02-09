#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_almost_equal

from regeneration.battle.test import FakeRand, quiet, assert_equal
from regeneration.battle.example import connect, tables, loader

from regeneration.battle import monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def testMonster():
    session = connect()

    species = session.query(tables.Form).filter_by(id=1).one()
    bulba = monster.Monster(species, 30, loader.natures, rand=FakeRand())
    assert_equal(bulba.ability.identifier, 'overgrow')
    assert_equal(bulba.gender.identifier, 'female')
    assert_equal(
            [m.kind.identifier for m in bulba.moves],
            'double-edge growth sweet-scent razor-leaf'.split(),
        )
    assert_equal(bulba.tameness, 70)
    assert not bulba.fainted
    assert bulba.name.endswith('saur')
    bulba.name = 'Testcase exhibit A'
    assert_equal(bulba.name, 'Testcase exhibit A')
    assert_equal(str(bulba), bulba.name)
    assert_equal(repr(bulba), '<Monster %s>' % bulba.name)
    bulba.name = None
    assert bulba.name.endswith('saur')

    def roundtrip(mon):
        saved = mon.save()
        loaded = monster.Monster.load(saved, loader)
        resaved = loaded.save()
        assert_equal(saved, resaved)
    roundtrip(bulba)

    bulba.shiny = False
    bulba.effort.hp = 100
    bulba.genes.def_ = 3
    bulba.name = 'Testcase exhibit B'
    bulba.item = loader.loadItem('fresh-water')
    bulba.gender = bulba.gender.opposite
    bulba.nature = loader.natures[1]
    bulba.ability = loader.loadAbility('own-tempo')
    bulba.tameness = 0
    bulba.hp = 0
    bulba.status = monster.Status.par
    bulba.setMoves([loader.loadMove('petal-dance'), loader.loadMove('bind')])
    bulba.setMove(0, loader.loadMove('pound'))
    assert_equal([move.kind.identifier for move in bulba.moves], ['pound', 'bind'])
    assert bulba.fainted
    bulba.recalculateStats()

    roundtrip(bulba)

    bulba.hp = 2
    bulba.effort.hp = 0
    bulba.level = 5
    bulba.recalculateStats()
    assert_equal(bulba.hp, 0)

    saved = bulba.save()
    del saved['genes']
    assert_equal(monster.Monster.load(saved, loader).genes.values(), [0] * 6)

    species = session.query(tables.Form).filter_by(id=137).one()
    gon = monster.Monster(species, 30, loader.natures, rand=FakeRand())
    assert_equal(gon.ability.identifier, 'trace')
    assert_equal(gon.gender.identifier, 'none')

@quiet
def testLoader():
    assert loader.loadForm('hypno').species.identifier == 'hypno'
    assert loader.loadMove('gust').identifier == 'gust'
    assert loader.loadNature('brave').identifier == 'brave'
    assert loader.loadAbility('minus').identifier == 'minus'
    assert loader.loadItem('stick').identifier == 'stick'
