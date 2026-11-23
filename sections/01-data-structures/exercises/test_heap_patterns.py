import math
import random
import signal
import tracemalloc

import pytest

from heap_patterns import assign_jobs, merge_sorted, top_k


@pytest.fixture(autouse=True)
def time_limit(request):
    """Heap solutions finish each test in about a second at most. Scanning
    every worker or every list front takes minutes (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is something scanning all k lists or all workers for every item?")

    old = signal.signal(signal.SIGALRM, boom)
    # the two million-item tests get more room, so a heap written in pure Python passes too
    signal.alarm({"test_assign_many_workers": 20, "test_top_k_big_k": 10}.get(request.node.name, 5))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class C:
    """A value that counts every comparison made with it (class-wide)."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        C.cmps += 1
        return other.v

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __eq__(self, o): return isinstance(o, C) and self.v == self._o(o)
    __hash__ = None


class Pulls:
    """Wrap an iterable and count, across all wrappers in a group, how many
    items have been pulled."""

    def __init__(self, items, tally):
        self.it, self.tally = iter(items), tally

    def __iter__(self):
        return self

    def __next__(self):
        x = next(self.it)
        self.tally[0] += 1
        return x


# 1. top_k
def test_top_k_examples():
    assert top_k(iter([4, 9, 1, 7, 3, 8]), 3) == [9, 8, 7]
    assert top_k(iter([5, 1]), 3) == [5, 1]
    assert top_k(iter([]), 2) == []
    assert top_k(iter([1, 2, 3]), 0) == []
    assert top_k(iter([2, 2, 2, 1]), 2) == [2, 2]
    assert top_k([3, 1, 2], 1) == [3]
    assert top_k(iter("banana"), 2) == ["n", "n"]


def test_top_k_only_requires_less_than():
    class LtOnly:
        __slots__ = ("v",)

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            return self.v < other.v

    got = top_k((LtOnly(v) for v in [4, 9, 1, 7, 3, 8, 9]), 3)
    assert [x.v for x in got] == [9, 9, 8]


def test_top_k_random():
    rng = random.Random(1)
    for _ in range(300):
        data = [rng.randint(-20, 20) for _ in range(rng.randint(0, 40))]
        k = rng.randint(1, 10)
        assert top_k(iter(data), k) == sorted(data, reverse=True)[:k], (data, k)


def test_top_k_streams_with_few_comparisons_and_little_memory():
    n, k = 100_000, 100
    vals = random.Random(9).sample(range(10 * n), n)
    gen = (C(v) for v in vals)  # each item is created as it's pulled
    C.cmps = 0
    tracemalloc.start()
    try:
        got = top_k(gen, k)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert [x.v for x in got] == sorted(vals, reverse=True)[:k]
    assert C.cmps <= 3 * n, f"{C.cmps:,} comparisons for {n:,} items ({C.cmps / n:.1f} each): most items should need one comparison with the root"
    assert peak <= 1_000_000, f"peak memory {peak:,} bytes: is the whole stream being kept?"


def test_top_k_rising_stream_costs_log_k_per_item():
    n, k = 20_000, 100  # every item beats the root, so every item gets in
    C.cmps = 0
    got = top_k((C(v) for v in range(n)), k)
    assert [x.v for x in got] == list(range(n - 1, n - k - 1, -1))
    budget = 3 * math.log2(k) * n
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} rising items (budget {budget:,.0f}): is it re-scanning all k kept items?"


def test_top_k_big_k():
    # k = 500,000 kept items and a rising stream, so every item gets in.
    # A heap does O(log k) per item (a pure-Python one takes about 2 s);
    # a sorted list shifts about k items per insert and takes over a minute.
    n, k = 1_000_000, 500_000
    got = top_k(iter(range(n)), k)
    assert len(got) == k and got[0] == n - 1 and got[-1] == n - k
    assert all(got[i] == n - 1 - i for i in range(0, k, 997))


# 2. merge_sorted
def test_merge_examples():
    assert list(merge_sorted([iter([1, 4, 9]), iter([2, 3]), iter([])])) == [1, 2, 3, 4, 9]
    assert list(merge_sorted([])) == []
    assert list(merge_sorted([iter([]), iter([])])) == []
    assert list(merge_sorted([iter([1, 1]), iter([1])])) == [1, 1, 1]
    assert list(merge_sorted([iter(["a", "c"]), iter(["b"])])) == ["a", "b", "c"]


def test_merge_random():
    rng = random.Random(4)
    for _ in range(200):
        lists = [sorted(rng.randint(0, 30) for _ in range(rng.randint(0, 8))) for _ in range(rng.randint(0, 6))]
        assert list(merge_sorted([iter(x) for x in lists])) == sorted(v for x in lists for v in x)


def test_merge_equal_items_do_not_compare_iterators():
    class Job:  # equal priorities from different lists must not crash a tuple comparison
        def __init__(self, p):
            self.p = p

        def __lt__(self, other):
            return self.p < other.p

        def __eq__(self, other):  # equal jobs: a tuple comparison moves on to the next field
            return self.p == other.p

        __hash__ = None

    lists = [[Job(1), Job(3)], [Job(1), Job(2)], [Job(3)]]
    assert [j.p for j in merge_sorted([iter(x) for x in lists])] == [1, 1, 2, 3, 3]


def test_merge_only_requires_less_than():
    class LtOnly:
        __slots__ = ("v",)

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            return self.v < other.v

    lists = [[LtOnly(1), LtOnly(4)], [LtOnly(1), LtOnly(3)], [LtOnly(2)]]
    assert [x.v for x in merge_sorted([iter(xs) for xs in lists])] == [1, 1, 2, 3, 4]


def test_merge_is_lazy():
    tally = [0]
    k = 50
    inputs = [Pulls(range(i, 10_000_000, k), tally) for i in range(k)]  # far too big to read all of it
    gen = merge_sorted(inputs)
    for m in range(1, 501):
        assert next(gen) == m - 1
        assert tally[0] <= k + m, f"after {m} outputs, {tally[0]:,} items were pulled: only pull from the list you just took from"


def test_merge_works_on_endless_inputs():
    def endless(start, step):
        while True:
            yield start
            start += step

    gen = merge_sorted([endless(0, 3), endless(1, 3), endless(2, 3)])
    assert [next(gen) for _ in range(30)] == list(range(30))


def test_merge_costs_log_k_per_item():
    k, each = 256, 200
    rng = random.Random(6)
    lists = [sorted(rng.sample(range(10 ** 7), each)) for _ in range(k)]
    C.cmps = 0
    out = [x.v for x in merge_sorted([iter([C(v) for v in lst]) for lst in lists])]
    total = k * each
    assert out == sorted(v for lst in lists for v in lst)
    budget = total * (4 * math.log2(k) + 8)
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {total:,} items from {k} lists (budget {budget:,.0f}): is it scanning every front?"


# 3. assign_jobs
def brute_assign(durations, workers):
    free = [0] * workers
    out = []
    for d in durations:
        w = min(range(workers), key=lambda i: (free[i], i))
        out.append((w, free[w]))
        free[w] += d
    return out


def test_assign_example():
    assert assign_jobs([1, 2, 3, 4, 5], 2) == [(0, 0), (1, 0), (0, 1), (1, 2), (0, 4)]
    assert assign_jobs([], 3) == []
    assert assign_jobs([5, 5, 5], 1) == [(0, 0), (0, 5), (0, 10)]
    assert assign_jobs([1, 1], 4) == [(0, 0), (1, 0)]


def test_assign_ties_go_to_the_lowest_worker():
    assert assign_jobs([2, 2, 2, 2, 2, 2], 3) == [(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2)]
    assert assign_jobs([0, 0, 3], 2) == [(0, 0), (0, 0), (0, 0)]


def test_assign_random():
    rng = random.Random(8)
    for _ in range(200):
        durs = [rng.randint(0, 9) for _ in range(rng.randint(0, 30))]
        w = rng.randint(1, 6)
        assert assign_jobs(durs, w) == brute_assign(durs, w), (durs, w)


def test_assign_many_workers():
    n, w = 1_000_000, 500_000
    got = assign_jobs([1] * n, w)
    # Every job takes 1: round j sends jobs to workers 0..w-1 in order, all starting at time j.
    assert len(got) == n
    assert got[:3] == [(0, 0), (1, 0), (2, 0)] and got[w] == (0, 1) and got[-1] == (w - 1, n // w - 1)
    assert all(got[j] == (j % w, j // w) for j in range(0, n, 997))


def test_assign_varying_durations_large():
    # Varying durations exercise non-uniform sift depths across 10,000 workers.
    rng = random.Random(19)
    n, w = 60_000, 10_000
    durs = [rng.randint(1, 50) for _ in range(n)]
    got = assign_jobs(durs, w)
    assert len(got) == n
    # Verify schedule invariants: every assignment starts at that worker's current free time,
    # and start times are monotonically non-decreasing.
    free = [0] * w
    prev_start = 0
    for d, (worker, start) in zip(durs, got):
        assert 0 <= worker < w
        assert start == free[worker]
        assert start >= prev_start
        prev_start = start
        free[worker] += d
    assert max(free) - min(free) <= 50, "greedy earliest-free assignment keeps worker finish times within max job duration"
