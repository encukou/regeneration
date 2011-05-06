#! /usr/bin/env python
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

        self.battle_stats = session.query(tables.Stat).order_by(
                tables.Stat.id).all()

        self.permanent_stats = [s for s in self.battle_stats if
                not s.is_battle_only]

    def load_form(self, identifier, form_identifier=None):
        query = self.session.query(tables.PokemonForm)
        query = query.join(tables.PokemonForm.pokemon)
        query = query.join(tables.Pokemon.species)
        query = query.filter(tables.PokemonForm.form_identifier == form_identifier)
        query = query.filter(tables.PokemonSpecies.identifier == identifier)
        return query.one()

    def load_by_identifier(self, table, identifier):
        key = self.session, table, identifier
        try:
            return self._identifier_cache[key]
        except KeyError:
            query = self.session.query(table)
            query = query.filter(table.identifier == identifier)
            result = query.one()
            self._identifier_cache[key] = result
            return result

    def load_move(self, identifier):
        return self.load_by_identifier(tables.Move, identifier)

    def load_nature(self, identifier):
        return self.load_by_identifier(tables.Nature, identifier)

    def load_ability(self, identifier):
        return self.load_by_identifier(tables.Ability, identifier)

    def load_item(self, identifier):
        return self.load_by_identifier(tables.Item, identifier)

    def load_stat(self, identifier):
        return self.load_by_identifier(tables.Stat, identifier)

    def load_struggle(self):
        return self.load_move('struggle')

    def load_types(self, identifiers):
        results = []
        for name in names:
            return self.load_type(identifiers)


loader = Loader(connect())

FormTable = tables.PokemonForm
FormTable.monster = FormTable.pokemon
tables.Pokemon.monster_moves = tables.Pokemon.pokemon_moves
