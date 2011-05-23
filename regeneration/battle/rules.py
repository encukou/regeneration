#! /usr/bin/env python
# Encoding: UTF-8

from regeneration.battle.field import Field
from regeneration.battle.monster import Monster

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class ValidationError(ValueError): pass

class MonsterValidationError(ValidationError):
    def __init__(self, message, monster):
        super(MonsterValidationError, self).__init__(self, message)
        self.monster = monster

class MoveValidationError(ValidationError):
    def __init__(self, message, monster):
        super(MonsterValidationError, self).__init__(self, message)
        self.monster = monster

class Clause(object):
    def __init__(self, rules):
        self.rules = rules

    def init_battle(self, field):
        pass

    def validate_trainer(self, trainer):
        pass

class ValidationClause(Clause):
    def validate_trainer(self, trainer):
        for monster in trainer.team:
            return self.validate_monster(monster)
        return True

    def validate_monster(self, monster):
        for move in monster.moves:
            self.validate_move(move)

    def validate_move(self, move):
        pass

class MonsterValidationClause(ValidationClause):
    MonsterClass = Monster

    def validate_monster(self, monster):
        if not isinstance(monster, self.MonsterClass):
            raise MonsterValidationError('%s is of a wrong class' % monster,
                monster)

class Rules(object):
    FieldClass = Field
    MonsterClass = Monster
    format = [[0], [1]]

    default_clause_classes = [MonsterValidationClause]

    def __init__(self, loader, clauses=()):
        self.loader = loader
        self.clauses = list(clauses) + [c(self) for c
                in self.default_clause_classes]

    def validate_trainer(self, trainer):
        for clause in self.clauses:
            clause.validate_trainer(trainer)

    def field(self, *trainers, **field_args):
        for trainer in trainers:
            self.validate_trainer(trainer)
        sides = []
        for s in self.format:
            side = []
            for t in s:
                side.append(trainers[t])
            sides.append(side)
        field = self.FieldClass(self.loader, sides, **field_args)
        for clause in self.clauses:
            clause.init_battle(field)
        return field
