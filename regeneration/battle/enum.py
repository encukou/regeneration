#! /usr/bin/python
# Encoding: UTF-8

__copyright__ = 'Copyright 2009-2011, Petr Viktorin'
__license__ = 'MIT'
__email__ = 'encukou@gmail.com'

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
                raise ValueError(
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

    def __getattr__(self, identifier):
        if identifier.endswith('_'):
            return getattr(self, identifier.rstrip('_'))
        else:
            raise AttributeError(identifier)

    def __getitem__(self, number):
        if isinstance(number, basestring):
            # actually an identifier
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
        return self.identifier

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.identifier)

    @classmethod
    def _add(cls, identifier):
        number = len(cls)
        newitem = cls(number, identifier, _privateConstructor=True)
        setattr(cls, identifier, newitem)
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
