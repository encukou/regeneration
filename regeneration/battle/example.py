#! /usr/bin/python
# Encoding: UTF-8

import weakref

# For an example, we can use veekun's pokedex database.
from pokedex.db import tables, connect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Loader(object):
    _identifier_cache = weakref.WeakValueDictionary()

    def __init__(self, session):
        self.session = session

        self.natures = session.query(tables.Nature).all()

        self.battleStats = session.query(tables.Stat).order_by(
                tables.Stat.id).all()

        self.permanentStats = [s for s in self.battleStats if
                not s.is_battle_only]

    def loadForm(self, identifier, form_identifier=None):
        query = self.session.query(tables.PokemonForm)
        query = query.join(tables.PokemonForm.pokemon)
        query = query.join(tables.Pokemon.species)
        query = query.filter(tables.PokemonForm.form_identifier == form_identifier)
        query = query.filter(tables.PokemonSpecies.identifier == identifier)
        return query.one()

    def loadByIdentifier(self, table, identifier):
        key = self.session, table, identifier
        try:
            return self._identifier_cache[key]
        except KeyError:
            query = self.session.query(table)
            query = query.filter(table.identifier == identifier)
            result = query.one()
            self._identifier_cache[key] = result
            return result

    def loadMove(self, identifier):
        return self.loadByIdentifier(tables.Move, identifier)

    def loadNature(self, identifier):
        return self.loadByIdentifier(tables.Nature, identifier)

    def loadAbility(self, identifier):
        return self.loadByIdentifier(tables.Ability, identifier)

    def loadItem(self, identifier):
        return self.loadByIdentifier(tables.Item, identifier)

    def loadStat(self, identifier):
        return self.loadByIdentifier(tables.Stat, identifier)

    def loadStruggle(self):
        return self.loadMove('struggle')

    def loadTypes(self, identifiers):
        results = []
        for name in names:
            return self.loadType(identifiers)


loader = Loader(connect())

FormTable = tables.PokemonForm
FormTable.monster = FormTable.pokemon
tables.Pokemon.monster_moves = tables.Pokemon.pokemon_moves
