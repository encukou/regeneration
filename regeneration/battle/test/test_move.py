#! /usr/bin/python
# Encoding: UTF-8

from nose.tools import assert_equal, assert_almost_equal


from regeneration.battle.example import connect, tables
from regeneration.battle.test import quiet

from regeneration.battle import move

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

@quiet
def test_move():
    session = connect()
    pound = move.Move(session.query(tables.Move).filter_by(id=1).one())
    assert_equal(pound.power, 40)
    assert_equal(pound.pp, 35)
    assert_equal(pound.accuracy, 1)
    assert_equal(pound.priority, 0)
    assert_equal(pound.type.identifier, 'normal')
    assert_equal(pound.damage_class.identifier, 'physical')

    pound.pp -= 1
    assert_equal(pound.pp, 34)
    assert_equal(pound.maxpp, 35)
    assert_equal(pound.kind.pp, 35)
    assert_equal(str(pound), "pound (34/35 PP)")

    triatk = move.Move(session.query(tables.Move).filter_by(id=161).one(), 12)
    assert_equal(triatk.pp, 12)
    assert_equal(triatk.maxpp, 12)
    assert_equal(triatk.kind.pp, 10)

    assert triatk.flags.protect
    assert not triatk.flags.contact
    # XXX: make non-existing flags raise an exception

    toxic = move.Move(session.query(tables.Move).filter_by(id=92).one())
    assert_equal(toxic.power, None)
    assert_equal(toxic.pp, 10)
    assert_almost_equal(toxic.accuracy, 0.9)

    hidden = move.Move(session.query(tables.Move).filter_by(id=237).one())
    assert_equal(hidden.power, None)
    assert_equal(hidden.pp, 15)
    assert_equal(hidden.accuracy, 1)

    dance = move.Move(session.query(tables.Move).filter_by(id=14).one())
    assert_equal(dance.power, None)
    assert_equal(dance.pp, 30)
    assert_equal(dance.accuracy, None)
