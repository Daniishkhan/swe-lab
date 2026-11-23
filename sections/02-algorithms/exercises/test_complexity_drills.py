import math
import random

import pytest

from complexity_drills import DynamicArray, count_pairs_with_sum, fast_power, has_duplicate


# 1. has_duplicate
class Song:
    """A hashable item that counts every comparison (== or <) made on it."""

    cmps = 0

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        return hash(self.v)

    def __eq__(self, other):
        Song.cmps += 1
        return self.v == other.v

    def __lt__(self, other):
        Song.cmps += 1
        return self.v < other.v


def test_has_duplicate_small():
    assert has_duplicate([3, 1, 4, 1]) is True
    assert has_duplicate([3, 1, 4]) is False
    assert has_duplicate([]) is False
    assert has_duplicate([42]) is False
    assert has_duplicate([-1, 1]) is False
    assert has_duplicate([-1, -1]) is True
    assert has_duplicate(["a", "b", "a"]) is True


def test_has_duplicate_counts_comparisons():
    n = 2000
    songs = [Song(i) for i in range(n)]
    random.Random(1).shuffle(songs)  # shuffled, so a sort can't get a free ride on sorted input
    Song.cmps = 0
    assert has_duplicate(songs) is False  # no duplicates: the worst case, every item is checked
    # A set needs (almost) no comparisons. Comparing pairs needs ~2,000,000; sorting ~20,000.
    assert Song.cmps <= 2 * n, f"{Song.cmps} comparisons for n={n}: something compares pairs (or sorts)"


# 2. DynamicArray
def test_dynamic_array_basics():
    a = DynamicArray()
    assert len(a) == 0
    assert a.capacity == 1
    for i in range(10):
        a.append(i * i)
    assert len(a) == 10
    assert [a[i] for i in range(10)] == [i * i for i in range(10)]
    assert a.capacity >= 10


def test_dynamic_array_index_errors():
    empty = DynamicArray()
    with pytest.raises(IndexError):
        empty[0]
    a = DynamicArray()
    for x in "abc":
        a.append(x)  # size 3, capacity 4
    with pytest.raises(IndexError):
        a[3]  # the slot exists in the block, but it isn't one of your items
    with pytest.raises(IndexError):
        a[-1]  # negative indexes aren't supported


def test_dynamic_array_grows_by_doubling():
    a = DynamicArray()
    caps = {a.capacity}
    for i in range(100):
        a.append(i)
        caps.add(a.capacity)
    assert caps == {1, 2, 4, 8, 16, 32, 64, 128}


def test_dynamic_array_amortized_copies():
    n = 100_000
    a = DynamicArray()
    for i in range(n):
        a.append(i)
        # Checked after every append, so a slow growth rule fails fast instead of running for minutes.
        assert a.copies < 2 * (i + 1), f"{a.copies} copies after {i + 1} appends: not amortized O(1)"
    assert a[n - 1] == n - 1
    assert a.copies > 0, "count every item you copy in self.copies"


# 3. count_pairs_with_sum
class CountingList:
    """A read-only list that counts how many times it's read."""

    def __init__(self, data):
        self._data = list(data)
        self.reads = 0

    def __len__(self):
        return len(self._data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            raise TypeError("no slicing: slicing copies, and copies hide work")
        self.reads += 1
        return self._data[i]

    def __iter__(self):
        for x in self._data:
            self.reads += 1
            yield x


class Val:
    """A number that counts every +, - and comparison done with it. Copying the list can't hide these."""

    ops = 0
    cmps = 0

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _raw(o):
        return o.v if isinstance(o, Val) else o

    def __add__(self, o):
        Val.ops += 1
        return self.v + self._raw(o)

    __radd__ = __add__

    def __sub__(self, o):
        Val.ops += 1
        return self.v - self._raw(o)

    def __rsub__(self, o):
        Val.ops += 1
        return o - self.v

    def __eq__(self, o):
        Val.cmps += 1
        return self.v == self._raw(o)

    def __lt__(self, o):
        Val.cmps += 1
        return self.v < self._raw(o)

    def __le__(self, o):
        Val.cmps += 1
        return self.v <= self._raw(o)

    def __gt__(self, o):
        Val.cmps += 1
        return self.v > self._raw(o)

    def __ge__(self, o):
        Val.cmps += 1
        return self.v >= self._raw(o)

    def __hash__(self):
        raise TypeError("Val is unhashable: use sorted two pointers for O(1) extra space")


def brute_pairs(nums, target):
    return sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == target)


def test_count_pairs_examples():
    assert count_pairs_with_sum([1, 2, 3, 4, 5, 6], 7) == 3
    assert count_pairs_with_sum([1, 2, 3], 100) == 0
    assert count_pairs_with_sum([], 5) == 0
    assert count_pairs_with_sum([3], 6) == 0
    assert count_pairs_with_sum([-3, -1, 0, 2, 4], 1) == 2


def test_count_pairs_matches_brute_force():
    rng = random.Random(3)
    for _ in range(100):
        nums = sorted(rng.sample(range(-50, 50), rng.randint(0, 20)))
        t = rng.randint(-60, 60)
        assert count_pairs_with_sum(nums, t) == brute_pairs(nums, t)


def test_count_pairs_reads_linear():
    n = 2000
    data = CountingList(range(0, 2 * n, 2))  # 0, 2, 4, ...
    assert count_pairs_with_sum(data, 2 * n) == 999
    assert data.reads <= 2 * n + 10, f"{data.reads} reads for n={n}: a nested loop would be ~{n * n // 2}"
    # Also test a no-match target so both pointers don't advance together
    data2 = CountingList(range(0, 2 * n, 2))
    assert count_pairs_with_sum(data2, 2 * n + 1) == 0
    assert data2.reads <= 2 * n + 10, f"{data2.reads} reads for n={n} on no-match target"


def test_count_pairs_additions_linear():
    n = 2000
    data = [Val(x) for x in range(0, 2 * n, 2)]
    Val.ops = 0
    Val.cmps = 0
    assert count_pairs_with_sum(data, 2 * n) == 999
    assert Val.ops <= 2 * n, f"{Val.ops} additions for n={n}: checking every pair would be ~{n * n // 2}"
    assert Val.cmps <= 2 * n, f"{Val.cmps} comparisons for n={n}: binary-searching each item would be ~{n * 11}"


# 4. fast_power
class Num:
    """A number that counts every multiplication, and refuses ** and pow()."""

    mults = 0

    def __init__(self, v):
        self.v = v

    def __mul__(self, o):
        Num.mults += 1
        return Num(self.v * (o.v if isinstance(o, Num) else o))

    __rmul__ = __mul__

    def __pow__(self, *args):
        raise TypeError("don't use ** or pow(): build it from multiplications")

    __rpow__ = __pow__


def test_fast_power_values():
    assert fast_power(2, 10)[0] == 1024
    assert fast_power(3, 0) == (1, 0)
    assert fast_power(7, 1)[0] == 7
    assert fast_power(5, 13)[0] == 5 ** 13
    assert fast_power(-2, 3)[0] == -8
    assert fast_power(0, 5)[0] == 0
    assert fast_power(0, 0)[0] == 1


@pytest.mark.parametrize("exp", [1, 2, 15, 16, 1000, 100_000])
def test_fast_power_logarithmic(exp):
    Num.mults = 0
    result, reported = fast_power(Num(3), exp)
    assert (result.v if isinstance(result, Num) else result) == 3 ** exp
    assert reported == Num.mults, f"you reported {reported} multiplications but did {Num.mults}"
    assert Num.mults <= 2 * math.log2(exp) + 2, f"{Num.mults} multiplications for exp={exp}"
