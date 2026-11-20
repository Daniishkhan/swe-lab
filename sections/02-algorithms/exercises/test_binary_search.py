import itertools
import math
import random

import pytest

from binary_search import max_min_gap, min_ship_capacity, search_range, search_rotated


class TooMuchWork(AssertionError):
    pass


class Reads:
    """A read-only sequence that counts every item read. Gives up past `budget`, so a slow answer fails fast."""

    def __init__(self, values, budget=10_000_000):
        self._v = list(values)
        self.n = 0
        self.budget = budget

    def _tick(self, k=1):
        self.n += k
        if self.n > self.budget:
            raise TooMuchWork(f"over {self.budget:,} reads for n={len(self._v):,}: that's not O(log n)")

    def __len__(self):
        return len(self._v)

    def __getitem__(self, i):
        if isinstance(i, slice):
            out = self._v[i]
            self._tick(len(out))
            return out
        self._tick()
        return self._v[i]

    def __iter__(self):
        for x in self._v:
            self._tick()
            yield x

    def __repr__(self):
        return f"Reads({self._v[:10]}{'...' if len(self._v) > 10 else ''})"


def read_limit(n):
    return 6 * math.ceil(math.log2(n + 1)) + 6


class Ops:
    count = 0
    budget = 10**9


class Num(int):
    """An int that counts every comparison, +, and - done with it. Results of + and - are plain ints."""

    def _t(self):
        Ops.count += 1
        if Ops.count > Ops.budget:
            raise TooMuchWork(f"over {Ops.budget:,} operations: trying answers one by one is too slow")

    def __lt__(self, o): self._t(); return int.__lt__(self, o)
    def __le__(self, o): self._t(); return int.__le__(self, o)
    def __gt__(self, o): self._t(); return int.__gt__(self, o)
    def __ge__(self, o): self._t(); return int.__ge__(self, o)
    def __eq__(self, o): self._t(); return int.__eq__(self, o)
    def __ne__(self, o): self._t(); return int.__ne__(self, o)
    def __add__(self, o): self._t(); return int.__add__(self, o)
    def __radd__(self, o): self._t(); return int.__radd__(self, o)
    def __sub__(self, o): self._t(); return int.__sub__(self, o)
    def __rsub__(self, o): self._t(); return int.__rsub__(self, o)
    __hash__ = int.__hash__


def nums(values):
    return [Num(v) for v in values]


def measure(fn, *args, budget):
    """Run fn with operation counting on; return (result as plain int, operations used)."""
    Ops.count, Ops.budget = 0, budget
    try:
        out = fn(*args)
        used = Ops.count
    finally:
        Ops.count, Ops.budget = 0, 10**9
    return int(out), used


# 4. search_range
def brute_range(vals, t):
    hits = [i for i, v in enumerate(vals) if v == t]
    return (hits[0], hits[-1]) if hits else (-1, -1)


@pytest.mark.parametrize("vals, t, expected", [
    ([5, 7, 7, 8, 8, 10], 8, (3, 4)),
    ([5, 7, 7, 8, 8, 10], 6, (-1, -1)),
    ([5, 7, 7, 8, 8, 10], 5, (0, 0)),
    ([5, 7, 7, 8, 8, 10], 10, (5, 5)),
    ([5, 7, 7, 8, 8, 10], 4, (-1, -1)),
    ([5, 7, 7, 8, 8, 10], 11, (-1, -1)),
    ([], 3, (-1, -1)),
    ([1], 1, (0, 0)),
    ([1], 0, (-1, -1)),
    ([1], 2, (-1, -1)),
    ([2, 2, 2], 2, (0, 2)),
    ([1, 2, 2], 2, (1, 2)),
    ([2, 2, 3], 2, (0, 1)),
])
def test_search_range_examples(vals, t, expected):
    assert tuple(search_range(Reads(vals), t)) == expected


def test_search_range_matches_brute_force():
    rnd = random.Random(1)
    for _ in range(600):
        vals = sorted(rnd.randint(0, 9) for _ in range(rnd.randint(0, 20)))
        t = rnd.randint(-1, 10)
        assert tuple(search_range(Reads(vals), t)) == brute_range(vals, t), f"nums={vals}, target={t}"


def _range_cases():
    n = 100_000
    rnd = random.Random(2)
    spread = sorted(rnd.randint(0, 999) for _ in range(n))
    run = [1] * 47_500 + [5] * 5_000 + [9] * 47_500
    return [
        ("all equal", [7] * n, 7),
        ("about 100 copies", spread, spread[n // 2]),
        ("missing, in the middle", [2 * i for i in range(n)], 50_001),
        ("smaller than all", spread, -5),
        ("bigger than all", spread, 1_000),
        ("a run of 5,000", run, 5),
        ("first item", [2 * i for i in range(n)], 0),
        ("last item", [2 * i for i in range(n)], 2 * (n - 1)),
    ]


@pytest.mark.parametrize("label, vals, t", _range_cases(), ids=[c[0] for c in _range_cases()])
def test_search_range_is_log_n(label, vals, t):
    limit = read_limit(len(vals))
    seq = Reads(vals, budget=50 * limit)
    assert tuple(search_range(seq, t)) == brute_range(vals, t)
    assert seq.n <= limit, f"{seq.n} reads on '{label}' (n={len(vals):,}, limit {limit}): walking along a run is O(n)"


# 5. search_rotated
def rotate(vals, r):
    return vals[r:] + vals[:r]


@pytest.mark.parametrize("vals, t, expected", [
    ([4, 5, 6, 7, 0, 1, 2], 0, 4),
    ([4, 5, 6, 7, 0, 1, 2], 3, -1),
    ([4, 5, 6, 7, 0, 1, 2], 4, 0),
    ([4, 5, 6, 7, 0, 1, 2], 2, 6),
    ([4, 5, 6, 7, 0, 1, 2], 7, 3),
    ([], 1, -1),
    ([1], 1, 0),
    ([1], 0, -1),
    ([3, 1], 1, 1),
    ([3, 1], 3, 0),
    ([1, 3], 3, 1),
    ([1, 2, 3, 4, 5], 4, 3),
])
def test_search_rotated_examples(vals, t, expected):
    assert search_rotated(Reads(vals), t) == expected


def test_search_rotated_every_small_case():
    for n in range(0, 10):
        base = [2 * i for i in range(n)]
        for r in range(max(n, 1)):
            vals = rotate(base, r)
            for t in range(-1, 2 * n + 1):
                want = vals.index(t) if t in vals else -1
                assert search_rotated(Reads(vals), t) == want, f"nums={vals}, target={t}"


def test_search_rotated_is_log_n():
    n = 100_000
    base = [2 * i for i in range(n)]
    limit = 8 * math.ceil(math.log2(n + 1)) + 8
    for r in [0, 1, n // 3, n // 2, n - 1]:
        vals = rotate(base, r)
        for t in [vals[0], vals[-1], 0, 2 * (n - 1), vals[n // 2], 2 * r + 1, -1, 2 * n]:
            seq = Reads(vals, budget=50 * limit)
            want = (n - r + t // 2) % n if t % 2 == 0 and 0 <= t < 2 * n else -1
            assert search_rotated(seq, t) == want, f"rotated by {r}, target {t}"
            assert seq.n <= limit, f"{seq.n} reads (n={n:,}, rotated by {r}, target {t}); limit {limit}"


# 6. min_ship_capacity
def brute_ship(weights, days):
    """Try every way to cut the line into at most `days` pieces."""
    n, best = len(weights), sum(weights)
    for parts in range(1, min(days, n) + 1):
        for cuts in itertools.combinations(range(1, n), parts - 1):
            bounds = (0,) + cuts + (n,)
            best = min(best, max(sum(weights[a:b]) for a, b in zip(bounds, bounds[1:])))
    return best


@pytest.mark.parametrize("weights, days, expected", [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, 15),
    ([3, 2, 2, 4, 1, 4], 3, 6),
    ([1, 2, 3, 1, 1], 4, 3),
    ([10], 1, 10),
    ([10], 5, 10),
    ([4, 4, 4], 1, 12),
    ([4, 4, 4], 3, 4),
    ([4, 4, 4], 10, 4),
    ([1, 1, 1, 9], 2, 9),
])
def test_min_ship_capacity_examples(weights, days, expected):
    got, _ = measure(min_ship_capacity, nums(weights), days, budget=10**7)
    assert got == expected


def test_min_ship_capacity_matches_brute_force():
    rnd = random.Random(3)
    for _ in range(300):
        w = [rnd.randint(1, 20) for _ in range(rnd.randint(1, 8))]
        d = rnd.randint(1, len(w) + 1)
        got, _ = measure(min_ship_capacity, nums(w), d, budget=10**7)
        assert got == brute_ship(w, d), f"weights={w}, days={d}"


# The big-input answers below were computed once, outside the repo, by two
# independent reference solutions (so the check you're asked to write isn't
# printed here). The inputs are seeded, so they never change.
@pytest.mark.parametrize("days, expected", [(1, 986_310), (10, 100_266), (300, 3_575)])
def test_min_ship_capacity_is_n_log_sum(days, expected):
    rnd = random.Random(4 + days)
    n = 2000
    w = [rnd.randint(1, 1000) for _ in range(n)]
    limit = 4 * n * (math.ceil(math.log2(sum(w))) + 2)
    got, used = measure(min_ship_capacity, nums(w), days, budget=3 * limit)
    assert got == expected, f"got capacity {got} for days={days}; the smallest that works is {expected}"
    assert used <= limit, f"{used:,} operations for n={n} (limit {limit:,}): binary search the capacity"


# 7. max_min_gap
def brute_gap(positions, k):
    return max(min(b - a for a, b in zip(c, c[1:])) for c in itertools.combinations(sorted(positions), k))


@pytest.mark.parametrize("positions, k, expected", [
    ([1, 2, 8, 4, 9], 3, 3),
    ([1, 2, 3, 4, 7], 3, 3),
    ([5, 4, 3, 2, 1, 1000000000], 2, 999999999),
    ([10, 1], 2, 9),
    ([1, 3, 6, 10], 4, 2),
    ([0, 100, 1, 99, 50], 3, 50),
    ([-10, 20, -3, 4], 3, 14),
])
def test_max_min_gap_examples(positions, k, expected):
    got, _ = measure(max_min_gap, nums(positions), k, budget=10**7)
    assert got == expected


def test_max_min_gap_matches_brute_force():
    rnd = random.Random(5)
    for _ in range(300):
        p = rnd.sample(range(0, 60), rnd.randint(2, 8))
        k = rnd.randint(2, len(p))
        got, _ = measure(max_min_gap, nums(p), k, budget=10**7)
        assert got == brute_gap(p, k), f"positions={p}, k={k}"


# Answers computed once outside the repo, like the shipping ones above.
@pytest.mark.parametrize("k, expected", [(2, 999_743_664), (20, 52_114_666), (1000, 503_063)])
def test_max_min_gap_is_fast(k, expected):
    rnd = random.Random(6 + k)
    n = 2000
    p = rnd.sample(range(0, 10**9), n)
    s = sorted(p)
    span = s[-1] - s[0]
    limit = int(2 * n * math.log2(n) + 4 * n * (math.ceil(math.log2(span)) + 2))
    got, used = measure(max_min_gap, nums(p), k, budget=3 * limit)
    assert got == expected, f"got {got} for k={k}; the largest smallest-gap is {expected}"
    assert used <= limit, f"{used:,} operations for n={n} (limit {limit:,}): sort once, then binary search the gap"
