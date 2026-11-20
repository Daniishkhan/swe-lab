import math
import random
import signal

import pytest

from fenwick_tree import FenwickTree


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second with O(log n) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: does a loop never end (index 0?), or does something scan the whole list?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class N:
    """A number that counts every +, - and comparison done with it (class-wide).
    Mixing with plain ints works, so an array that starts as 0s is fine."""

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
    def __lt__(self, o): return self.v < self._op(o)
    def __le__(self, o): return self.v <= self._op(o)
    def __gt__(self, o): return self.v > self._op(o)
    def __ge__(self, o): return self.v >= self._op(o)
    def __eq__(self, o): return self.v == self._op(o)
    def __int__(self): raise TypeError("don't convert the items to int: use + and - only")
    __float__ = __int__
    __index__ = __int__
    __hash__ = None
    def __repr__(self): return f"N({self.v})"


def val(x):
    return x.v if isinstance(x, N) else x


def brute_find(a, target):
    run = 0
    for i, x in enumerate(a):
        run += x
        if run >= target:
            return i
    return len(a)


def test_example():
    f = FenwickTree.from_list([5, 2, 9, 1, 4])
    assert len(f) == 5
    assert f.prefix_sum(3) == 16
    assert f.range_sum(1, 4) == 12
    f.add(2, -6)
    assert f.range_sum(0, 5) == 15
    assert f.find_prefix(8) == 2


def test_starts_at_zero():
    f = FenwickTree(6)
    assert len(f) == 6
    assert [f.prefix_sum(k) for k in range(7)] == [0] * 7
    f.add(0, 3)
    f.add(5, 4)
    assert [f.prefix_sum(k) for k in range(7)] == [0, 3, 3, 3, 3, 3, 7]
    assert f.range_sum(1, 5) == 0 and f.range_sum(0, 6) == 7


def test_empty_and_single():
    f = FenwickTree(0)
    assert len(f) == 0 and f.prefix_sum(0) == 0 and f.range_sum(0, 0) == 0
    assert f.find_prefix(1) == 0
    g = FenwickTree.from_list([7])
    assert g.prefix_sum(1) == 7 and g.range_sum(0, 0) == 0
    assert g.find_prefix(7) == 0 and g.find_prefix(8) == 1


def test_from_list_does_not_change_input():
    data = [4, -1, 3, 0, 2]
    f = FenwickTree.from_list(data)
    assert data == [4, -1, 3, 0, 2]
    assert [f.prefix_sum(k) for k in range(6)] == [0, 4, 3, 6, 6, 8]


def test_bad_index_raises():
    f = FenwickTree.from_list([1, 2, 3])
    for i in (-1, 3, 10):
        with pytest.raises(IndexError):
            f.add(i, 1)
    assert f.prefix_sum(3) == 6, "a rejected add must not change anything"


def test_random_against_a_plain_list():
    rng = random.Random(10)
    for _ in range(60):
        n = rng.randint(1, 40)
        a = [rng.randint(-9, 9) for _ in range(n)]
        if rng.random() < 0.5:
            f = FenwickTree.from_list(a)
        else:  # start empty and load it with adds
            f = FenwickTree(n)
            for i, x in enumerate(a):
                f.add(i, x)
        for _ in range(80):
            op = rng.random()
            if op < 0.4:
                i, d = rng.randrange(n), rng.randint(-9, 9)
                a[i] += d
                f.add(i, d)
            elif op < 0.7:
                k = rng.randint(0, n)
                assert f.prefix_sum(k) == sum(a[:k])
            else:
                lo = rng.randint(0, n)
                hi = rng.randint(lo, n)
                assert f.range_sum(lo, hi) == sum(a[lo:hi]), (a, lo, hi)


def test_find_prefix_random():
    rng = random.Random(11)
    for _ in range(80):
        n = rng.randint(1, 50)
        a = [rng.randint(0, 4) for _ in range(n)]
        f = FenwickTree.from_list(a)
        for _ in range(20):
            i = rng.randrange(n)
            d = rng.randint(0, 3)
            a[i] += d
            f.add(i, d)
            t = rng.randint(1, sum(a) + 2)
            assert f.find_prefix(t) == brute_find(a, t), (a, t)


def test_find_prefix_with_zeros_and_ties():
    f = FenwickTree.from_list([0, 0, 3, 0, 0, 2, 0, 0])
    assert [f.find_prefix(t) for t in range(1, 7)] == [2, 2, 2, 5, 5, 8]


def test_works_on_non_ints():
    f = FenwickTree.from_list([0.5, 0.25, 0.125])
    assert f.prefix_sum(3) == 0.875
    f.add(1, 0.25)
    assert f.range_sum(1, 3) == 0.625


def test_from_list_is_linear():
    n = 2 ** 15
    rng = random.Random(3)
    vals = [rng.randint(0, 100) for _ in range(n)]
    items = [N(v) for v in vals]
    N.ops = 0
    f = FenwickTree.from_list(items)
    built = N.ops
    assert built < 3 * n, f"{built:,} operations to build from {n:,} items ({built / n:.1f} each): each slot only needs to pass its total to one other slot"
    for k in (0, 1, 1000, n // 2 + 7, n):
        assert val(f.prefix_sum(k)) == sum(vals[:k])


def test_add_and_prefix_sum_cost_log_n():
    n = 2 ** 16
    rng = random.Random(4)
    f = FenwickTree(n)
    a = [0] * n
    m = 3000
    budget = m * (math.log2(n) + 2)
    N.ops = 0
    for _ in range(m):
        i, d = rng.randrange(n), rng.randint(1, 9)
        a[i] += d
        f.add(i, N(d))
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} adds on {n:,} items (budget {budget:,.0f}): does add walk more than one path?"
    pref = [0]
    for x in a:
        pref.append(pref[-1] + x)
    N.ops = 0
    for _ in range(m):
        k = rng.randint(0, n)
        assert val(f.prefix_sum(k)) == pref[k]
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} prefix sums on {n:,} items (budget {budget:,.0f}): is it adding items one by one?"


def test_range_sum_costs_log_n():
    n = 2 ** 16
    rng = random.Random(5)
    vals = [rng.randint(-50, 50) for _ in range(n)]
    pref = [0]
    for x in vals:
        pref.append(pref[-1] + x)
    f = FenwickTree.from_list([N(v) for v in vals])
    m = 3000
    budget = m * (2 * math.log2(n) + 4)
    N.ops = 0
    for _ in range(m):
        lo = rng.randint(0, n)
        hi = rng.randint(lo, n)
        assert val(f.range_sum(lo, hi)) == pref[hi] - pref[lo]
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} range sums (budget {budget:,.0f}): two prefix walks and one subtraction is enough"


def test_find_prefix_costs_log_n():
    n = 2 ** 16
    rng = random.Random(6)
    vals = [rng.randint(0, 3) for _ in range(n)]
    f = FenwickTree.from_list([N(v) for v in vals])
    total = sum(vals)
    run, firsts = 0, {}
    for i, x in enumerate(vals):
        for t in range(run + 1, run + x + 1):
            firsts[t] = i
        run += x
    m = 2000
    budget = m * (3 * math.log2(n) + 6)
    N.ops = 0
    for _ in range(m):
        t = rng.randint(1, total)
        assert f.find_prefix(t) == firsts[t]
    assert N.ops <= budget, f"{N.ops:,} operations for {m:,} find_prefix calls (budget {budget:,.0f}): walk down by powers of two instead of binary searching with prefix_sum"
