import itertools
import math
import random
import signal

import pytest

from greedy_intervals import fewest_stabs, fewest_to_cover


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with the intended approach (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something re-scanning every interval for every pick?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class C:
    """A value that counts every comparison made with it (class-wide)."""

    __slots__ = ("_v",)
    cmps = 0

    def __init__(self, v):
        self._v = v

    def _o(self, other):
        C.cmps += 1
        return other._v if isinstance(other, C) else other

    def __lt__(self, o): return self._v < self._o(o)
    def __le__(self, o): return self._v <= self._o(o)
    def __gt__(self, o): return self._v > self._o(o)
    def __ge__(self, o): return self._v >= self._o(o)
    def __eq__(self, o): return self._v == self._o(o)
    def __ne__(self, o): return self._v != self._o(o)
    def __hash__(self): return hash(self._v)
    def __repr__(self): return f"C({self._v})"


def val(x):
    return x._v if isinstance(x, C) else x


def budget(n):
    return 3 * n * math.log2(n) + 10 * n


# ---------------------------------------------------------------- checkers
def stabbed_all(intervals, points):
    pts = sorted(points)
    for s, e in intervals:
        # some point p with s <= p <= e: look at the first point >= s
        lo, hi = 0, len(pts)
        while lo < hi:
            mid = (lo + hi) // 2
            if pts[mid] < s:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(pts) or pts[lo] > e:
            return False
    return True


def covers(clips, picked, T):
    reach = 0
    for s, e in sorted(clips[i] for i in picked):
        if s > reach:
            return False
        reach = max(reach, e)
    return reach >= T


def brute_stabs(intervals):
    ends = sorted({e for _, e in intervals})  # some best answer uses only right ends
    for r in range(len(ends) + 1):
        for combo in itertools.combinations(ends, r):
            if stabbed_all(intervals, combo):
                return r


def brute_cover(clips, T):
    for r in range(1, len(clips) + 1):
        for combo in itertools.combinations(range(len(clips)), r):
            if covers(clips, combo, T):
                return r
    return None


def check_stabs(data, got, want_count):
    got = [val(p) for p in got]
    assert got == sorted(got), "return the points in increasing order"
    assert stabbed_all(data, got), f"some interval has no point in it: {data} -> {got}"
    assert len(got) == want_count, f"{len(got)} points, but {want_count} are enough: {data} -> {got}"


def check_cover(clips, T, got, want_count):
    if want_count is None:
        assert got is None, f"[0, {T}] can't be covered by {clips}, expected None, got {got}"
        return
    assert got is not None, f"[0, {T}] can be covered with {want_count} clips: {clips}"
    assert len(set(got)) == len(got), "an index appears twice"
    assert all(isinstance(i, int) and 0 <= i < len(clips) for i in got), f"bad index in {got}"
    assert covers(clips, got, T), f"clips {got} leave a gap in [0, {T}]: {clips}"
    assert len(got) == want_count, f"{len(got)} clips, but {want_count} are enough: {clips}"


# ---------------------------------------------------------------- big inputs, answers known by construction
def stab_instance(k, n, seed):
    """k anchor points 100 i + 50. k short intervals around them don't touch each
    other, so at least k points are needed; every other interval contains an
    anchor, so the k anchors are enough. The answer is exactly k."""
    rng = random.Random(seed)
    anchors = [100 * i + 50 for i in range(k)]
    data = [(p - 1, p + 1) for p in anchors]
    while len(data) < n:
        p = rng.choice(anchors)
        data.append((p - rng.randint(0, 120), p + rng.randint(0, 120)))
    rng.shuffle(data)
    return data


def cover_instance(k, n, seed, hole=None):
    """k chain clips [10 i, 10 i + 12]: the point 10 i + 5 is in chain clip i only,
    so all k are needed and they cover [0, 10 (k - 1) + 12]. Every other clip sits
    inside one chain clip, so it can never replace two. The answer is exactly k.
    With hole=i, chain clip i and everything inside it are left out: no cover."""
    rng = random.Random(seed)
    chain = [(10 * i, 10 * i + 12) for i in range(k)]
    data = [c for i, c in enumerate(chain) if i != hole]
    while len(data) < n:
        i = rng.randrange(k)
        if i == hole:
            continue
        s = 10 * i + rng.randint(0, 11)
        data.append((s, rng.randint(s + 1, 10 * i + 12)))
    rng.shuffle(data)
    return data, 10 * (k - 1) + 12


# ---------------------------------------------------------------- 1. fewest_stabs
def test_stabs_examples():
    check_stabs([(10, 16), (2, 8), (1, 6), (7, 12)], fewest_stabs([(10, 16), (2, 8), (1, 6), (7, 12)]), 2)
    check_stabs([(1, 2), (3, 4), (5, 6), (7, 8)], fewest_stabs([(1, 2), (3, 4), (5, 6), (7, 8)]), 4)
    assert [val(p) for p in fewest_stabs([(1, 2), (2, 3)])] == [2], "closed intervals: touching at 2 counts"
    assert fewest_stabs([]) == []
    check_stabs([(5, 5)], fewest_stabs([(5, 5)]), 1)


def test_stabs_nested_and_duplicates():
    data = [(1, 10), (2, 3), (2, 3), (4, 5), (1, 10)]
    check_stabs(data, fewest_stabs(data), 2)
    data = [(0, 100), (40, 41), (60, 61)]
    check_stabs(data, fewest_stabs(data), 2)  # the long one is not the one to aim at


def test_stabs_random_small():
    rng = random.Random(10)
    for _ in range(300):
        data = []
        for _ in range(rng.randint(1, 8)):
            s = rng.randint(0, 20)
            data.append((s, s + rng.randint(0, 6)))
        check_stabs(data, fewest_stabs(data), brute_stabs(data))


def test_stabs_does_not_modify_input():
    data = [(10, 16), (2, 8), (1, 6), (7, 12)]
    fewest_stabs(data)
    assert data == [(10, 16), (2, 8), (1, 6), (7, 12)]


def test_stabs_comparisons():
    n, k = 2000, 400
    data = stab_instance(k, n, seed=11)
    C.cmps = 0
    got = fewest_stabs([(C(s), C(e)) for s, e in data])
    used = C.cmps
    check_stabs(data, got, k)
    assert used <= budget(n), f"{used:,} comparisons for {n:,} intervals (budget {budget(n):,.0f}): sort once, then one pass"


# ---------------------------------------------------------------- 2. fewest_to_cover
def test_cover_examples():
    clips = [(0, 2), (4, 6), (8, 10), (1, 9), (1, 5), (5, 9)]
    got = fewest_to_cover(clips, 10)
    check_cover(clips, 10, got, 3)
    assert sorted(got) == [0, 2, 3]
    assert fewest_to_cover([(0, 1), (1, 2)], 5) is None
    assert fewest_to_cover([(-3, 8)], 5) == [0]
    assert fewest_to_cover([], 5) is None


def test_cover_touching_and_gaps():
    check_cover([(0, 4), (4, 7)], 7, fewest_to_cover([(0, 4), (4, 7)], 7), 2)
    assert fewest_to_cover([(1, 9)], 5) is None, "nothing covers 0"
    assert fewest_to_cover([(0, 3), (4, 9)], 9) is None, "(3, 4) is a gap"
    clips = [(0, 3), (0, 6), (2, 5), (5, 9), (6, 8)]
    check_cover(clips, 9, fewest_to_cover(clips, 9), 2)


def test_cover_random_small():
    rng = random.Random(20)
    for _ in range(300):
        clips = []
        for _ in range(rng.randint(1, 9)):
            s = rng.randint(-2, 14)
            clips.append((s, s + rng.randint(1, 7)))
        T = rng.randint(1, 15)
        check_cover(clips, T, fewest_to_cover(clips, T), brute_cover(clips, T))


def test_cover_does_not_modify_input():
    clips = [(5, 9), (0, 6), (2, 5)]
    fewest_to_cover(clips, 9)
    assert clips == [(5, 9), (0, 6), (2, 5)]


def test_cover_comparisons():
    n, k = 2000, 300
    clips, T = cover_instance(k, n, seed=21)
    C.cmps = 0
    got = fewest_to_cover([(C(s), C(e)) for s, e in clips], C(T))
    used = C.cmps
    check_cover(clips, T, got, k)
    assert used <= budget(n), f"{used:,} comparisons for {n:,} clips (budget {budget(n):,.0f}): sort once, then one pass"


def test_cover_big_impossible():
    n, k = 2000, 300
    clips, T = cover_instance(k, n, seed=22, hole=137)
    C.cmps = 0
    got = fewest_to_cover([(C(s), C(e)) for s, e in clips], C(T))
    assert got is None, "nothing covers 1375, so there is no cover"
    assert C.cmps <= budget(n)
