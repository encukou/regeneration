#! /usr/bin/env python
# Encoding: UTF-8

import weakref

__copyright__ = 'Copyright 2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

"""This is an example of how a real Loader class would look like.

Most of the stuff here are dummies, but it should give you an idea of what's
needed.
"""

class Dummy(object):
    def __init__(self, **attrs):
        for name, value in attrs.items():
            setattr(self, name, value)

class Loader(object):
    _identifier_cache = weakref.WeakValueDictionary()

    def __init__(self):
        self.battle_stats = [Dummy(identifier=s) for s in
            'hp attack defense special-attack special-defense speed '
            'accuracy evasion'.split()]

        self.permanent_stats = self.battle_stats[:6]

        self._dummy_type = dummy = Dummy()
        dummy.damage_efficacies=[Dummy(damage_type=dummy, target_type=dummy,
                damage_factor=100)]

    def load_form(self, identifier, form_identifier=None):
        dummy = Dummy(
                form_identifier=form_identifier,
                monster=Dummy(
                        items=[],
                        abilities=[None],
                        types=[self._dummy_type],
                    ),
                species=Dummy(
                        id=233 if identifier[-1].isdigit() else 137,
                        gender_rate=0,
                        base_happiness=0,
                        identifier=identifier,
                    ),
            )
        return dummy

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
        return Dummy(
                target=Dummy(identifier='selected-battler'),
                priority=0,
                power=50,
                type=self._dummy_type,
                accuracy=100,
                damage_class=Dummy(identifier='physical'),
                name='Tackle',
                identifier=identifier,
                pp=35,
                effect_chance=0,
            )

    def load_nature(self, identifier):
        return Dummy(identifier=identifier)

    def load_ability(self, identifier):
        return Dummy(identifier=identifier)

    def load_item(self, identifier):
        return Dummy(identifier=identifier)

    def load_stat(self, identifier):
        stat, = [s for s in self.permanent_stats if s.identifier == identifier]
        return stat

    def load_struggle(self):
        return self.load_move('struggle')

    def load_type(self, identifier):
        return self._dummy_type

    def load_types(self, identifiers):
        results = []
        for identifier in identifiers:
            results.append(self.load_type(identifier))
        return results

loader = Loader()
