#! /usr/bin/python
# Encoding: UTF-8

import random

__copyright__ = "Copyright 2009-2010, Petr Viktorin"
__license__ = "MIT"
__email__ = "encukou@gmail.com"

class _EnumMetaclass(type):
    def __init__(cls, name, bases, dct):
        super(_EnumMetaclass, cls).__init__(name, bases, dct)
        if bases == (object,):
            # Enum itself; don't try adding identifiers
            return
        try:
            identifiers = cls.identifiers
            cls._identifiers = []
        except:
            raise TypeError(
                    'Enum class %s does not have an identifiers field.'
                        % cls.__name__
                )
        else:
            if isinstance(identifiers, basestring):
                # Despite what Guido may think, treating strings as iterables
                # in a dynamic language is just dumb.
                raise TypeError(
                        "identifiers of enum class %s may not be a string. "
                        "Did you forget a .split()?" % cls.__name__
                    )
            base, = bases
            if base is not Enum:
                for v in base:
                    setattr(cls, v.identifier, v)
                    cls._identifiers.append(v)
            for v in identifiers:
                cls._add(v)

    def __iter__(self):
        return iter(self._identifiers)

    def __len__(self):
        return len(self._identifiers)

    def __getitem__(self, number):
        if isinstance(number, basestring):
            try:
                return getattr(self, number)
            except AttributeError:
                raise KeyError(number)
        return self._identifiers[number]


class Enum(object):
    """ An enumeration.

    Each class has attributes, which are instances of the class.
    Each instance has a identifier and a number.
    An enum class can be used in a list-ish way: it's iterable, has a length,
    and supports getting items by number (as well as identifier).
    For an example, see the Stat class.

    To make a new enumeration, subclass Enum and give it a "identifiers" class
    attribute, which should be a list of strings. These become identifiers for
    the new subclasses.

    Currently you can use only single inheritance when subclassing;
    the items are concatenated when you do this.
    """

    __metaclass__ = _EnumMetaclass

    startnumber = 0

    def __init__(self, number, identifier, **args):
        assert '_privateConstructor' in args, "This constructor is private."
        self.identifier = identifier
        self.number = number

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    @classmethod
    def _add(cls, name):
        number = len(cls)
        newitem = cls(number, name, _privateConstructor=True)
        setattr(cls, name, newitem)
        cls._identifiers.append(newitem)

    def __lt__(self, other):
        return self.number < other.number

    def __gt__(self, other):
        return self.number > other.number

    def __eq__(self, other):
        return self.number == other.number

    def __le__(self, other):
        return self.number <= other.number

    def __ge__(self, other):
        return self.number >= other.number

    def __ne__(self, other):
        return self.number != other.number


class Stat(Enum):
    """ An enumeration of pokémon stats
    """
    # XXX: Use veekun DB objects; but handle BattleStat correctly
    identifiers = "hp atk def spd sat sde".split()
    names = "HP,Attack,Defense,Speed,Special Attack,Special Defense".split(',')


class BattleStat(Stat):
    identifiers = "acc eva".split()
    names = "Accuracy,Evasion".split(',')

for stat, name in zip(
        BattleStat,
        Stat.names + BattleStat.names,
    ):
    stat.name = name


class Stats(dict):
    """A collection of Stat values

    Basically a hybrid that supports both attribute and item access to get
    the values.
    Its keys are Enum objects.
    """
    _statEnum = Stat

    @classmethod
    def Random(cls, min, max, rand=random, statEnum=Stat):
        self = cls()
        self._statEnum = statEnum
        for stat in statEnum:
            self.addItem(stat, rand.randint(min, max))
        return self

    def __getitem__(self, item):
        try:
            return super(Stats, self).__getitem__(item)
        except KeyError:
            return super(Stats, self).__getitem__(self._statEnum[item])

    def __setitem__(self, item, value):
        """Setter. You can use Enum objects, numbers or names for item.

        Only pre-existing keys can be set using []. Use addItem() if you're
        sure you want to add a new item.
        """
        if not item in self:
            item = self._statEnum[item]
        super(Stats, self).__setitem__(item, value)

    def __getattr__(self, attr):
        return self[self._statEnum[attr]]

    def __setattr__(self, attr, value):
        if attr[:1] == '_':
            self.__dict__[attr] = value
        else:
            self[self._statEnum[attr]] = value

    def addItem(self, item, value):
        """As __setitem__, but allows setting keys that don't exist yet.

        Be sure to use a Enum object as the key, not ints/strings"""
        super(Stats, self).__setitem__(item, value)

    def __iter__(self):
        return (x[1] for x in sorted(self.items(), key=lambda x: x[0]))

    @property
    def compact_str(self):
        return " ".join(s.name+":"+str(self[s]) for s in self._statEnum)

    def __str__(self):
        return "<Stats: {"+", ".join(str(s)+": "+str(self[s]) for s in self._statEnum)+"}>"

    def save(self):
        return dict((k.name, v) for k, v in self.items())

    @classmethod
    def load(cls, dct):
        return cls(
                ([s for s in Stat if s.name==k][0], v) for k, v in dct.items()
            )

    def __deepcopy__(self, memo):
        return self.__class__(self)

