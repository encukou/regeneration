#! /usr/bin/env python
# Encoding: UTF-8

import random

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

class StatAttributeAccessMixin(object):
    def _stat_by_identifier(self, identifier):
        identifier = identifier.replace('_', '-')
        return [s for s in self if s.identifier == identifier][0]

    def __getattr__(self, attr):
        return self[self._stat_by_identifier(attr)]

    def __setattr__(self, attr, value):
        if attr[0] == '_':
            super(StatAttributeAccessMixin, self).__setattr__(attr, value)
        else:
            self[self._stat_by_identifier(attr)] = value


class Stats(dict, StatAttributeAccessMixin):
    """A collection of stat values

    Besides the special __init__, it also allows attribute access to the stats,
    and saving/loading to/from a simple dict.
    """
    def __init__(self, stat_objects, min=0, max=None, rand=random):
        """Create a new set of stats

        If statObjects is a dict-like object, stats will get copied from it.
        Otherwise, it must be a list of stats to use as keys.

        If max is given, the values will be random between min and max
            (as given by rand)
        Otherwise, they will all get set to min, or 0 by default.
        """
        try:
            dict.__init__(self, stat_objects)
        except TypeError:
            for stat in stat_objects:
                if max is None:
                    self[stat] = min
                else:
                    self[stat] = rand.randint(min, max)

    def __str__(self):
        return "<Stats: {0}>".format(", ".join("%s: %s" %
                (k.identifier, v) for k, v in self.items()))

    def save(self):
        return dict((k.identifier, v) for k, v in self.items())

    @classmethod
    def load(cls, dct, stat_objects):
        loaded = cls(stat_objects)
        for identifier, value in dct.items():
            setattr(loaded, identifier, value)
        return loaded
