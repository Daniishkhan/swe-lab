import itertools
import math
import random
import signal

import pytest

from job_scheduling import best_weighted_order, most_on_time


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with the intended approach (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something trying every order, or re-scanning for every job?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class N:
    """A number that counts every comparison made with it (class-wide).
    Arithmetic gives another N, so keys computed from it are counted too."""

    __slots__ = ("_v",)
    cmps = 0

    def __init__(self, v):
        self._v = v

    @staticmethod
    def _u(o):
        return o._v if isinstance(o, N) else o

    def _c(self, o):
        N.cmps += 1
        return N._u(o)

    def __lt__(self, o): return self._v < self._c(o)
    def __le__(self, o): return self._v <= self._c(o)
    def __gt__(self, o): return self._v > self._c(o)
    def __ge__(self, o): return self._v >= self._c(o)
    def __eq__(self, o): return self._v == self._c(o)
    def __ne__(self, o): return self._v != self._c(o)
    def __hash__(self): return hash(self._v)
    def __add__(self, o): return N(self._v + N._u(o))
    __radd__ = __add__
    def __sub__(self, o): return N(self._v - N._u(o))
    def __rsub__(self, o): return N(N._u(o) - self._v)
    def __mul__(self, o): return N(self._v * N._u(o))
    __rmul__ = __mul__
    def __truediv__(self, o): return N(self._v / N._u(o))
    def __rtruediv__(self, o): return N(N._u(o) / self._v)
    def __neg__(self): return N(-self._v)
    def __repr__(self): return f"N({self._v})"


def wrap(jobs):
    return [(N(a), N(b)) for a, b in jobs]


# ---------------------------------------------------------------- checkers and brute force
def all_on_time(jobs, order):
    t = 0
    for i in order:
        t += jobs[i][0]
        if t > jobs[i][1]:
            return False
    return True


def check_on_time(jobs, got, want):
    assert all(isinstance(i, int) and 0 <= i < len(jobs) for i in got), f"bad index in {got}"
    assert len(set(got)) == len(got), "an index appears twice"
    assert all_on_time(jobs, got), f"running {got} in that order makes a job late: {jobs}"
    assert len(got) == want, f"{len(got)} jobs on time, but {want} is possible: {jobs}"


def brute_on_time(jobs):
    n = len(jobs)
    for r in range(n, -1, -1):
        for combo in itertools.combinations(range(n), r):
            if all_on_time(jobs, sorted(combo, key=lambda i: jobs[i][1])):
                return r


def weighted_cost(jobs, order):
    t = cost = 0
    for i in order:
        t += jobs[i][0]
        cost += jobs[i][1] * t
    return cost


def check_order(jobs, got, want_cost):
    assert sorted(got) == list(range(len(jobs))), f"return every index exactly once, got {got}"
    c = weighted_cost(jobs, got)
    assert c == want_cost, f"order {got} costs {c}, but {want_cost} is possible: {jobs}"


def brute_order(jobs):
    return min(weighted_cost(jobs, p) for p in itertools.permutations(range(len(jobs))))


# ---------------------------------------------------------------- 1. most_on_time
def test_on_time_examples():
    jobs = [(3, 5), (2, 4), (1, 2), (4, 7)]
    got = most_on_time(jobs)
    check_on_time(jobs, got, 3)
    assert got == [2, 1, 3]
    jobs = [(100, 200), (200, 1300), (1000, 1250), (2000, 3200)]
    check_on_time(jobs, most_on_time(jobs), 3)
    assert most_on_time([(5, 3)]) == []
    assert most_on_time([]) == []
    assert most_on_time([(2, 2)]) == [0], "finishing exactly at the deadline is on time"


def test_on_time_drop_the_longest_not_the_newest():
    # deadline order: (1,3), (5,6), (2,6), (2,7). Taking (5,6) blocks two short jobs.
    jobs = [(5, 6), (1, 3), (2, 7), (2, 6)]
    check_on_time(jobs, most_on_time(jobs), 3)
    # one long early job blocks five short ones
    jobs = [(6, 6)] + [(1, 7)] * 5
    check_on_time(jobs, most_on_time(jobs), 5)


def test_on_time_random_small():
    rng = random.Random(50)
    for _ in range(400):
        jobs = [(rng.randint(1, 6), rng.randint(0, 15)) for _ in range(rng.randint(1, 9))]
        check_on_time(jobs, most_on_time(jobs), brute_on_time(jobs))


def test_on_time_does_not_modify_input():
    jobs = [(3, 5), (2, 4), (1, 2), (4, 7)]
    most_on_time(jobs)
    assert jobs == [(3, 5), (2, 4), (1, 2), (4, 7)]


def big_on_time_jobs():
    rng = random.Random(51)
    return [(rng.randint(1, 100), rng.randint(1, 30_000)) for _ in range(3000)]


def test_on_time_comparisons():
    jobs = big_on_time_jobs()
    n = len(jobs)
    N.cmps = 0
    got = most_on_time(wrap(jobs))
    used = N.cmps
    check_on_time(jobs, got, 1310)  # computed offline
    budget = 6 * n * math.log2(n)
    assert used <= budget, f"{used:,} comparisons for {n:,} jobs (budget {budget:,.0f}): sort once, keep the kept jobs in a heap"


# ---------------------------------------------------------------- 2. best_weighted_order
def test_weighted_examples():
    jobs = [(3, 1), (1, 2), (2, 2)]
    got = best_weighted_order(jobs)
    check_order(jobs, got, 14)
    assert got == [1, 2, 0]
    assert best_weighted_order([]) == []
    assert best_weighted_order([(4, 9)]) == [0]


def test_weighted_neither_shortest_nor_heaviest_first():
    # shortest first puts (1, 1) first; heaviest first puts (10, 11) first. Both lose.
    jobs = [(1, 1), (10, 11), (3, 5)]
    check_order(jobs, best_weighted_order(jobs), brute_order(jobs))
    jobs = [(2, 1), (3, 9), (1, 1), (4, 5)]
    check_order(jobs, best_weighted_order(jobs), brute_order(jobs))


def test_weighted_random_small():
    rng = random.Random(60)
    for _ in range(300):
        jobs = [(rng.randint(1, 9), rng.randint(1, 9)) for _ in range(rng.randint(1, 7))]
        check_order(jobs, best_weighted_order(jobs), brute_order(jobs))


def test_weighted_does_not_modify_input():
    jobs = [(3, 1), (1, 2), (2, 2)]
    best_weighted_order(jobs)
    assert jobs == [(3, 1), (1, 2), (2, 2)]


def big_weighted_jobs():
    rng = random.Random(61)
    return [(rng.randint(1, 1000), rng.randint(1, 1000)) for _ in range(3000)]


def test_weighted_comparisons():
    jobs = big_weighted_jobs()
    n = len(jobs)
    N.cmps = 0
    got = best_weighted_order(wrap(jobs))
    used = N.cmps
    check_order(jobs, got, 578_807_220_709)  # computed offline, exact fractions
    budget = 3 * n * math.log2(n)
    assert used <= budget, f"{used:,} comparisons for {n:,} jobs (budget {budget:,.0f}): one sort with the right key"
