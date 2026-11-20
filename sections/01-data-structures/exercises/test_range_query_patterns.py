import math
import random
import signal

import pytest

from range_query_patterns import RangeAdder, count_smaller_after


@pytest.fixture(autouse=True)
def time_limit():
    """A Fenwick tree finishes each test in about a second; comparing every
    pair takes minutes (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something comparing every pair, or walking a whole range?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class N:
    """A number that counts every + and - done with it (class-wide)."""

    __slots__ = ("v",)
    ops = 0

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, N) else x

    def _op(self, other):
        N.ops += 1
        return N._v(other)

    def __add__(self, o): return N(self.v + self._op(o))
    def __radd__(self, o): return N(self._op(o) + self.v)
    def __sub__(self, o): return N(self.v - self._op(o))
    def __rsub__(self, o): return N(self._op(o) - self.v)
    def __neg__(self):
        N.ops += 1
        return N(-self.v)
    def __eq__(self, o): return self.v == N._v(o)
    def __int__(self): raise TypeError("don't convert deltas to int: use + and - only")
    __float__ = __int__
    __index__ = __int__
    __hash__ = None
    def __repr__(self): return f"N({self.v})"


def val(x):
    return x.v if isinstance(x, N) else x


def brute_smaller(nums):
    return [sum(1 for y in nums[i + 1:] if y < x) for i, x in enumerate(nums)]


# 1. count_smaller_after
def test_count_smaller_examples():
    assert count_smaller_after([5, 2, 6, 1]) == [2, 1, 1, 0]
    assert count_smaller_after([]) == []
    assert count_smaller_after([7]) == [0]
    assert count_smaller_after([2, 2, 2]) == [0, 0, 0]
    assert count_smaller_after([3, 2, 1]) == [2, 1, 0]
    assert count_smaller_after([1, 2, 3]) == [0, 0, 0]
    assert count_smaller_after([-1, -1, -2]) == [1, 1, 0]


def test_count_smaller_huge_values():
    big = 10 ** 18
    assert count_smaller_after([big, -big, 0, big - 1]) == [3, 0, 0, 0]


def test_count_smaller_does_not_change_input():
    nums = [4, 1, 3, 1]
    out = count_smaller_after(nums)
    assert nums == [4, 1, 3, 1] and out == [3, 0, 1, 0]


def test_count_smaller_random():
    rng = random.Random(15)
    for _ in range(300):
        nums = [rng.randint(-8, 8) for _ in range(rng.randint(0, 40))]
        assert count_smaller_after(nums) == brute_smaller(nums), nums


def test_count_smaller_big():
    rng = random.Random(16)
    n = 100_000
    nums = [rng.randint(-10 ** 18, 10 ** 18) for _ in range(n)]
    nums[::7] = [rng.randint(-5, 5) for _ in range(len(nums[::7]))]  # some duplicates too
    got = count_smaller_after(nums)
    assert len(got) == n
    for i in range(0, n, 9973):  # spot-check against a direct count
        assert got[i] == sum(1 for y in nums[i + 1:] if y < nums[i])
    assert got[-1] == 0


# 2. RangeAdder
def test_range_adder_example():
    r = RangeAdder(5)
    r.add(1, 4, 10)
    r.add(0, 2, -3)
    assert [r.get(i) for i in range(5)] == [-3, 7, 10, 10, 0]


def test_range_adder_edges():
    r = RangeAdder(4)
    r.add(2, 2, 99)  # empty range: no change
    r.add(0, 4, 1)  # the whole list
    r.add(3, 4, 5)  # the last item only
    assert [r.get(i) for i in range(4)] == [1, 1, 1, 6]
    one = RangeAdder(1)
    one.add(0, 1, 2)
    assert one.get(0) == 2


def test_range_adder_random():
    rng = random.Random(17)
    for _ in range(80):
        n = rng.randint(1, 30)
        a = [0] * n
        r = RangeAdder(n)
        for _ in range(60):
            if rng.random() < 0.5:
                lo = rng.randint(0, n)
                hi = rng.randint(lo, n)
                d = rng.randint(-9, 9)
                for i in range(lo, hi):
                    a[i] += d
                r.add(lo, hi, d)
            else:
                i = rng.randrange(n)
                assert r.get(i) == a[i], (a, i)


def test_range_adder_costs_log_n():
    n = 2 ** 16
    rng = random.Random(18)
    r = RangeAdder(n)
    diff = [0] * (n + 1)
    m = 2000
    budget = m * (2 * math.log2(n) + 6)
    N.ops = 0
    for _ in range(m):
        lo = rng.randrange(n)
        hi = rng.randint(lo + 1, n)
        d = rng.randint(1, 9)
        diff[lo] += d
        diff[hi] -= d
        r.add(lo, hi, N(d))
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} range adds on {n:,} items (budget {budget:,.0f}): a range add should be two point changes"
    a, run = [], 0
    for i in range(n):
        run += diff[i]
        a.append(run)
    budget = m * (math.log2(n) + 3)
    N.ops = 0
    for _ in range(m):
        i = rng.randrange(n)
        assert val(r.get(i)) == a[i]
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} gets (budget {budget:,.0f}): get should be one prefix walk, not a sum of the whole difference array"
