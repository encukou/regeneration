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

    @staticmethod
    def filter(table, thing):
        return table.id == thing

    def loadForm(self, name, form=None):
        query = self.session.query(tables.PokemonForm)
        if form:
            query = query.filter(self.filter(tables.PokemonForm, form))
        else:
            query = query.filter(self.filter(tables.Pokemon, name))
            query = query.filter(
                    tables.PokemonForm.form_base_pokemon_id ==
                        tables.Pokemon.id
                )
        return query.one()

    def loadByName(self, table, name):
        query = self.session.query(table)
        query = query.filter(self.filter(table, name))
        return query.one()

    def loadMove(self, name):
        return self.loadByName(tables.Move, name)

    def loadNature(self, name):
        return self.loadByName(tables.Nature, name)

    def loadAbility(self, name):
        return self.loadByName(tables.Ability, name)

    def loadItem(self, name):
        return self.loadByName(tables.Item, name)


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
