#! /usr/bin/env python
# Encoding: UTF-8

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
    assert pound.power == 40
    assert pound.pp == 35
    assert pound.accuracy == 1
    assert pound.priority == 0
    assert pound.type.identifier == 'normal'
    assert pound.damage_class.identifier == 'physical'

    pound.pp -= 1
    assert pound.pp == 34
    assert pound.maxpp == 35
    assert pound.kind.pp == 35
    assert str(pound) == "pound (34/35 PP)"

    triatk = move.Move(session.query(tables.Move).filter_by(id=161).one(), 12)
    assert triatk.pp == 12
    assert triatk.maxpp == 12
    assert triatk.kind.pp == 10

    assert triatk.flags.protect
    assert not triatk.flags.contact
    # XXX: make non-existing flags raise an exception

    toxic = move.Move(session.query(tables.Move).filter_by(id=92).one())
    assert toxic.power == None
    assert toxic.pp == 10
    assert toxic.accuracy * 10 == 9  # 0.9

    hidden = move.Move(session.query(tables.Move).filter_by(id=237).one())
    assert hidden.power == None
    assert hidden.pp == 15
    assert hidden.accuracy == 1

    dance = move.Move(session.query(tables.Move).filter_by(id=14).one())
    assert dance.power == None
    assert dance.pp == 30
    assert dance.accuracy == None
