#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_equal, assert_almost_equal
import yaml
import difflib

from regeneration.battle.example import connect, tables, loader

from regeneration.battle import monster

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class FakeRand(object):
    def randint(self, a, b):
        return 0

    def choice(self, lst):
        return lst[0]

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
        if saved != resaved:
            for line in difflib.ndiff(
                    *(yaml.safe_dump(x).splitlines() for x in (saved, resaved))
                ):
                print line
        assert_equal(saved, resaved)
    roundtrip(bulba)

    bulba.shiny = False
    bulba.effort.hp = 100
    bulba.genes.def_ = 3
    bulba.name = 'Testcase exhibit B'
    bulba.item = loader.loadItem(30)
    bulba.gender = bulba.gender.opposite
    bulba.nature = loader.natures[1]
    bulba.ability = loader.loadAbility(20)
    bulba.tameness = 0
    bulba.hp = 0
    bulba.status = monster.Status.par
    bulba.setMoves([loader.loadMove(80), loader.loadMove(30)])
    bulba.setMove(0, loader.loadMove(1))
    assert_equal([move.kind.id for move in bulba.moves], [1, 30])
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

def testLoader():
    assert loader.loadForm(1).id == 1
    assert loader.loadMove(1).id == 1
    assert loader.loadNature(1).id == 1
    assert loader.loadAbility(1).id == 1
    assert loader.loadItem(1).id == 1
