import math
import random
import signal

import pytest

from skip_list import SkipList


@pytest.fixture(autouse=True)
def time_limit(request):
    """Each test takes well under a second with O(log n) operations, a few
    seconds for the 200,000-key test (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is something walking the whole bottom level?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20 if request.node.name == "test_many_ints" else 10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class K:
    """A key that counts every comparison made with it (class-wide) and can't
    be hashed, so it can't go in a dict or a set."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        K.cmps += 1
        return other.v

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __eq__(self, o): return isinstance(o, K) and self.v == self._o(o)
    def __ne__(self, o): return not (isinstance(o, K) and self.v == self._o(o))
    __hash__ = None
    def __repr__(self): return f"K({self.v})"


def make(seed=1, **kw):
    return SkipList(rng=random.Random(seed), **kw)


def vals(keys):
    return [k.v for k in keys]


def levels(s):
    out, i = [], 0
    while True:
        lv = s.level_keys(i)
        if not lv:
            return out
        out.append(lv)
        i += 1


def test_example():
    s = make()
    assert all(s.insert(x) for x in [30, 10, 50, 20, 40])
    assert s.insert(20) is False
    assert 20 in s and 35 not in s
    assert list(s) == [10, 20, 30, 40, 50]
    assert s.range_query(15, 40) == [20, 30, 40]
    assert s.remove(30) is True and s.remove(30) is False
    assert len(s) == 4
    assert s.level_keys(0) == [10, 20, 40, 50]


def test_empty_and_one():
    s = make()
    assert len(s) == 0 and list(s) == [] and 5 not in s
    assert s.remove(5) is False
    assert s.range_query(0, 10) == [] and s.level_keys(0) == []
    assert s.insert(5) is True
    assert list(s) == [5] and len(s) == 1 and 5 in s
    assert s.range_query(5, 5) == [5] and s.range_query(6, 9) == [] and s.range_query(9, 0) == []
    assert s.remove(5) is True
    assert len(s) == 0 and list(s) == [] and levels(s) == []
    assert s.insert(7) is True and list(s) == [7]


def test_matches_a_sorted_set():
    rng = random.Random(4)
    s, ref = make(5), set()
    for step in range(4000):
        x = rng.randint(0, 300)
        op = rng.random()
        if op < 0.5:
            assert s.insert(x) == (x not in ref)
            ref.add(x)
        elif op < 0.8:
            assert s.remove(x) == (x in ref)
            ref.discard(x)
        else:
            assert (x in s) == (x in ref)
        assert len(s) == len(ref)
        if step % 200 == 0:
            assert list(s) == sorted(ref)
    assert list(s) == sorted(ref)


def test_range_query_matches_brute_force():
    rng = random.Random(8)
    data = rng.sample(range(1000), 300)
    s = make(9)
    for x in data:
        s.insert(x)
    for _ in range(500):
        lo, hi = rng.randint(-50, 1050), rng.randint(-50, 1050)
        assert s.range_query(lo, hi) == sorted(x for x in data if lo <= x <= hi), (lo, hi)


def test_strings_and_tuples():
    s = make(2)
    for w in ["pear", "apple", "fig", "kiwi", "apple", "date"]:
        s.insert(w)
    assert list(s) == ["apple", "date", "fig", "kiwi", "pear"]
    assert s.range_query("b", "g") == ["date", "fig"]
    t = make(3)
    for pair in [(2, "b"), (1, "z"), (2, "a")]:
        t.insert(pair)
    assert list(t) == [(1, "z"), (2, "a"), (2, "b")]


@pytest.mark.parametrize("p", [0.5, 0.25])
def test_shape_is_a_skip_list(p):
    n = 4096
    keys = random.Random(6).sample(range(10 * n), n)
    s = SkipList(p=p, rng=random.Random(7))
    for x in keys:
        s.insert(x)
    lv = levels(s)
    assert lv and lv[0] == sorted(keys), "level 0 must hold every key, ascending"
    for i in range(1, len(lv)):
        assert lv[i] == sorted(lv[i]), f"level {i} isn't sorted"
        assert set(lv[i]) <= set(lv[i - 1]), f"level {i} has a key that level {i - 1} doesn't: towers must stand on the levels below"
    for i in range(1, len(lv)):
        want = n * p ** i
        if want < 200:
            break
        assert 0.7 * want <= len(lv[i]) <= 1.3 * want, (
            f"level {i} holds {len(lv[i])} keys; about n * p^{i} = {want:.0f} expected. Is each extra level a coin flip with probability p?")
    expect = math.log(n, 1 / p)
    assert expect - 4 <= len(lv) <= expect + 10, f"{len(lv)} levels for {n} keys at p = {p} (about {expect:.0f} expected)"


def test_max_level_caps_height():
    s = SkipList(max_level=3, rng=random.Random(1))
    for x in random.Random(2).sample(range(5000), 1000):
        s.insert(x)
    assert s.level_keys(3) == [] and s.level_keys(2), "max_level=3 means levels 0, 1 and 2 only"
    assert len(s.level_keys(0)) == 1000


@pytest.mark.parametrize("order", ["random", "rising", "falling"])
def test_insert_costs_log_n(order):
    n = 4096
    vs = list(range(n))
    if order == "random":
        random.Random(3).shuffle(vs)
    elif order == "falling":
        vs.reverse()
    keys = [K(v) for v in vs]
    s = make(11)
    K.cmps = 0
    for k in keys:
        assert s.insert(k) is True
    per = K.cmps / n
    budget = 4 * math.log2(n) + 20
    assert per <= budget, f"{per:.1f} comparisons per insert ({order} order), budget {budget:.0f}: does each insert walk the bottom level?"
    assert vals(s) == sorted(vs)


def test_contains_and_remove_cost_log_n():
    n = 4096
    rng = random.Random(12)
    vs = rng.sample(range(0, 4 * n, 2), n)  # even numbers; odd ones are absent
    s = make(13)
    for v in vs:
        s.insert(K(v))
    budget = 4 * math.log2(n) + 20
    probes = [K(rng.randrange(4 * n)) for _ in range(n)]
    K.cmps = 0
    present = set(vs)
    hits = sum(1 for k in probes if k in s)
    assert hits == sum(1 for k in probes if k.v in present)
    assert K.cmps / n <= budget, f"{K.cmps / n:.1f} comparisons per lookup (budget {budget:.0f})"
    rng.shuffle(vs)
    K.cmps = 0
    for v in vs:
        assert s.remove(K(v)) is True
    assert K.cmps / n <= budget, f"{K.cmps / n:.1f} comparisons per remove (budget {budget:.0f})"
    assert len(s) == 0 and list(s) == []


def test_range_query_cost():
    n = 4096
    s = make(14)
    for v in random.Random(15).sample(range(n), n):
        s.insert(K(v))
    rng = random.Random(16)
    total, budget = 0, 0
    for _ in range(200):
        lo = rng.randrange(n - 20)
        K.cmps = 0
        got = s.range_query(K(lo), K(lo + 9))
        total += K.cmps
        budget += 4 * math.log2(n) + 20 + 2 * len(got)
        assert vals(got) == list(range(lo, lo + 10))
    assert total <= budget, f"{total:,} comparisons for 200 ranges (budget {budget:,.0f}): does the range start its walk at the head of level 0?"


def test_many_ints():
    rng = random.Random(17)
    data = [rng.randrange(10 ** 9) for _ in range(200_000)]
    s = make(18)
    for x in data:
        s.insert(x)
    assert len(s) == len(set(data))
    assert all(x in s for x in data[::4])
    assert sum(1 for x in range(10 ** 9 - 1000, 10 ** 9) if x in s) == sum(1 for x in set(data) if x >= 10 ** 9 - 1000)
