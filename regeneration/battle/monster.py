#! /usr/bin/python
# Encoding: UTF-8

import random

from regeneration.battle.stats import Stats
from regeneration.battle.enum import Enum
from regeneration.battle.gender import Gender
from regeneration.battle.move import Move

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class Monster(object):
    """ Represents an individual monster

    As such, it has a species (=dex entry), individual attributes (name, genes,
    effort, nature, ability, moveset with PPs, all that), and status attributes
    (current HP/PP, fixed status ailment).
    Attributes that are purely battle-specific (pseudo-status, Conversion
    temporary type, etc.) are not included here.

    The most important species attributes (e.g. types) are available directly
    on Monster, but most are accessible only through the species.

    If genes, effort, or nature are changed, be sure to call recalculateStats().
    """

    def __init__(self, form, level, loader, rand=random, _load_moves=True):
        """ Create a random Monster of the given species and level.

        The randomness corresponds to a typical random encounter; if any fields
        are supposed to be pre-set, set them after instantiation

        The natures argument is a list of all possible natures.

        The rand argument is used only in initialization.
        """

        self.form = form
        self.species = form.species
        self.level = level

        self.genes = Stats(loader.permanentStats, 0, 31, rand=rand)
        self.effort = Stats(loader.permanentStats)
        self.stats = Stats(loader.permanentStats)

        self.nature = rand.choice(loader.natures)

        self.hp = 0
        self.recalculateStats()
        self.hp = self.stats.hp

        self._name = None

        self.status = Status.ok

        self.gender = Gender.Random(self.species.species.gender_rate, rand=rand)

        self.tameness = self.species.species.base_happiness

        self.shiny = random.randint(0, 65535) < 8

        if _load_moves:
            self.setMoves(self._wildMovesAtLevel(level))

        try:
            self.item = rand.choice(self.species.items).item
        except IndexError:
            self.item = None

        self.ability = rand.choice(self.species.abilities)

    def setMoves(self, kinds):
        self.moves = [Move(kind) for kind in kinds]

    def setMove(self, i, kind):
        self.moves[i] = Move(kind)

    def recalculateStats(self):
        missingHp = self.stats.hp - self.hp
        for stat in self.genes:
            (pstat,) = (
                    pstat for pstat in self.species.stats
                    if pstat.stat.name == stat.name
                )
            base = pstat.base_stat
            gene = self.genes[stat]
            effort = self.effort[stat]
            level = self.level
            result = ((2 * base + gene + (effort // 4)) * level // 100 + 5)
            if stat.identifier == 'hp':
                result += level + 5
            else:
                statIdentifier = stat.name.lower().replace(' ', '-')
                if self.nature.increased_stat is pstat.stat:
                    result = int(result * 1.1)
                elif self.nature.decreased_stat is pstat.stat:
                    result = int(result * 0.9)
            self.stats[stat] = result
        self.hp = self.stats.hp - missingHp
        if self.hp < 0:
            self.hp = 0

    def rename(self, newName):
        self._name = newName

    name = property(
            fget=lambda self: self._name or self.species.name,
            fset=rename,
            fdel=lambda self: self.rename(None),
            doc="""Name of the monster. If set to None, the species' name is
            used, and evolution (or language changes) will change the apparent
            value.
            """
        )

    types = property(lambda self: self.species.types)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    @property
    def fainted(self):
        return self.hp <= 0

    def _wildMovesAtLevel(self, level):
        # XXX: This could be sped up if some magic is used so the underlying
        # query can be accessed => searching in SQL directly. Worth it?
        movelist = list(x for x
                in self.species.species_moves
                if x.level <= level and x.method.identifier == 'level-up')
        movelist.sort(
                key=lambda x: (
                        -x.version_group.generation.id,
                        -x.level,
                        x.order
                    )
            )
        seen = set()
        result = []
        for x in movelist:
            if x.move not in seen:
                seen.add(x.move)
                result.append(x.move)
                if(len(result) >= 4):
                    break
        return result

    def save(self):
        """Save the monster to a dict"""
        return dict(
                nickname=self._name,
                species=self.species.species.identifier,
                form=self.species.default_form.form_identifier,
                level=self.level,
                shiny=self.shiny,
                met='',
                item=self.item.identifier if self.item else None,
                gender=self.gender.identifier,
                nature=self.nature.identifier,
                ability=self.ability.identifier,
                genes=self.genes.save(),
                effort=self.effort.save(),
                tameness=self.tameness,
                hp=self.hp,
                status=self.status.identifier,
                moves=[
                        dict(
                            kind=move.kind.identifier,
                            pp=move.pp
                        )
                        for move
                        in self.moves
                    ],
            )

    @classmethod
    def load(cls, dct, loader):
        """Load the monster from a dict prepared by save().

        No checks are made on the validity of the data; this is by design.
        """
        get = dct.get
        rv = cls(
                loader.loadForm(get('species'), get('form', None)),
                get('level', 100),
                loader,
                rand = FakeRand(),
                _load_moves='moves' not in dct,
            )
        rv.name = get('nickname', None)
        rv.shiny = get('shiny', False)
        rv.met = get('met', '')
        rv.item = loader.loadItem(get('item')) if get('item') else None
        if 'gender' in dct:
            rv.gender = Gender[get('gender')]
        if 'nature' in dct:
            rv.nature = loader.loadNature(get('nature'))
        rv.ability = loader.loadAbility(get('ability'))
        if 'genes' in dct:
            rv.genes = Stats.load(get('genes'), loader.permanentStats)
        else:
            rv.genes = Stats(loader.permanentStats)
        if 'effort' in dct:
            rv.effort = Stats.load(get('effort'), loader.permanentStats)
        if 'tameness' in dct:
            rv.tameness = get('tameness')
        if 'status' in dct:
            rv.status = Status[get('status')]
        if 'moves' in dct:
            rv.moves = [
                    Move(
                        loader.loadMove(move_info['kind']),
                        move_info.get('pp', None),
                    )
                    for move_info in get('moves')
                ]
        rv.recalculateStats()
        if 'hp' in dct:
            rv.hp = get('hp')
        return rv

class Status(Enum):
    """ An enum of status ailments """

    identifiers = 'ok brn frz par psn slp fnt'.split()

class FakeRand(object):
    def randint(self, a, b):
        return (a + b) // 2

    def choice(self, lst):
        return lst[0]
