#! /usr/bin/python
# Encoding: UTF-8

# For an example, we can use veekun's pokedex database.
from pokedex.db import tables, connect

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Loader(object):
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
        query = self.session.query(table)
        query = query.filter(table.identifier == identifier)
        return query.one()

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

# Monkey-patches
# XXX: deal with these better

@property
def getIdentifier(self):
    return self.name.lower().replace(' ', '-')

def patchIdentifier(table):
    if not hasattr(table, 'identifier'):
        table.identifier = getIdentifier

patchIdentifier(tables.MoveDamageClass)
patchIdentifier(tables.Stat)
patchIdentifier(tables.Ability)
patchIdentifier(tables.PokemonMoveMethod)
patchIdentifier(tables.Move)
patchIdentifier(tables.Pokemon)
patchIdentifier(tables.PokemonForm)
patchIdentifier(tables.Nature)
patchIdentifier(tables.Type)

tables.Species = tables.Pokemon
tables.Species.species_moves = property(lambda self: self.pokemon_moves)
tables.Form = tables.PokemonForm
tables.Form.species = tables.Form.pokemon
