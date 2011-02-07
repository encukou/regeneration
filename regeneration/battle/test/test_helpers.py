import sys

from nose.tools import assert_equal, assert_raises

from regeneration.battle import stats

def assert_all_equal(head, *tail):
    for i, item in enumerate(tail):
        assert_equal(head, item,
                'Item %d (%r) is not equal to %r' % (i + 1, item, head)
            )

class Tee():
    def __init__(self, origstream):
        self.origstream = origstream
        self.writtenItems = []

    def write(self, str):
        self.origstream.write(str)
        self.writtenItems.append(str)

def quiet(func):
    def hushedTest(*args, **kwargs):
        sys.stdout = tee = Tee(sys.stdout)
        origStdout = sys.stdout
        func(*args, **kwargs)
        sys.stdout = origStdout
        assert_equal(tee.writtenItems, [], 'Test wrote to stdout')
    hushedTest.__name__ = func.__name__
    return hushedTest

@quiet
def test_stats():
    assert_equal(len(stats.Stat), 6)
    assert_equal(stats.Stat.sat.name, 'Special Attack')
    assert_equal(stats.Stat.sat.number, 4)
    assert_equal(
            [s.identifier for s in stats.Stat],
            'hp atk def spd sat sde'.split(),
        )

    assert_equal(len(stats.BattleStat), 8)
    assert_equal(
            [s.identifier for s in stats.BattleStat],
            'hp atk def spd sat sde acc eva'.split(),
        )

    assert_equal(
            [s.name for s in stats.Stat],
            'HP,Attack,Defense,Speed,Special Attack,Special Defense'.split(','),
        )

    class FakeRand():
        def randint(self, a, b):
            return a + b

    statdict = stats.Stats.Random(2, 4, rand=FakeRand())
    assert_equal(list(statdict), [6] * 6)

    assert_all_equal(statdict['hp'], statdict[0], statdict[stats.Stat.hp], 6)

    statdict['hp'] = 7
    assert_all_equal(7, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(6, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict[1] = 8
    assert_all_equal(7, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(8, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict[stats.Stat.hp] = 9
    assert_all_equal(9, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(8, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    statdict.atk = 10
    assert_all_equal(9, statdict['hp'], statdict[0], statdict[stats.Stat.hp])
    assert_all_equal(10, statdict['atk'], statdict[1], statdict[stats.Stat.atk])

    def set_foo():
        statdict['foo'] = 11
    assert_raises(KeyError, set_foo)

    def set_acc():
        statdict['acc'] = 11
    assert_raises(KeyError, set_acc)
