import itertools
import signal
from contextlib import contextmanager

import pytest

from py_idioms import (
    flatten_stream,
    make_multipliers,
    rank_candidates,
    transpose_and_filter,
    window_sums,
)


@contextmanager
def cap(seconds, hint):
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(f"over {seconds} s: {hint}")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------- rank_candidates

def test_rank_candidates_example():
    records = [
        ("b", 90, 5),
        ("a", 90, 5),
        ("c", 90, 2),
        ("d", None, 0),
        ("e", 95, 10),
    ]
    snapshot = list(records)
    assert rank_candidates(records) == ["e", "c", "a", "b"]
    assert records == snapshot


def test_rank_candidates_edges():
    assert rank_candidates([]) == []
    assert rank_candidates([("x", None, 1), ("y", None, 0)]) == []
    assert rank_candidates([("z", 0, 0), ("a", 0, 0)]) == ["a", "z"]
    assert rank_candidates([("neg", -5, 1), ("zero", 0, 99)]) == ["zero", "neg"]


# ---------------------------------------------------------------- transpose_and_filter

def test_transpose_and_filter_example():
    m = [[1, 5, 3], [4, 2, 6]]
    snapshot = [row[:] for row in m]
    assert transpose_and_filter(m, 3) == [[4], [5], [3, 6]]
    assert m == snapshot


def test_transpose_and_filter_edges():
    assert transpose_and_filter([], 0) == []
    assert transpose_and_filter([[], []], 0) == []
    assert transpose_and_filter([[1, 2], [3, 4]], 10) == [[], []]
    assert transpose_and_filter([[-5, 0, 5]], 0) == [[], [0], [5]]


# ---------------------------------------------------------------- make_multipliers

def test_make_multipliers_avoids_late_binding():
    fns = make_multipliers([2, 3, 10])
    assert len(fns) == 3
    assert [f(5) for f in fns] == [10, 15, 50]
    assert fns[0](7) == 14
    assert fns[1](-2) == -6


def test_make_multipliers_edges():
    assert make_multipliers([]) == []
    factors = [0, -1, 1]
    fns = make_multipliers(factors)
    factors[0] = 999  # mutating caller list after creation must not affect closures
    assert [f(9) for f in fns] == [0, -9, 9]
    gen_fns = make_multipliers(x for x in [4, 5])
    assert [f(3) for f in gen_fns] == [12, 15]


# ---------------------------------------------------------------- flatten_stream

def test_flatten_stream_nested_and_atomic_strings():
    data = [1, (2, [3, "hello", b"xy", "", b""]), [], [[4], (x for x in [5, 6])]]
    gen = flatten_stream(data)
    assert iter(gen) is gen, "flatten_stream should return a lazy iterator/generator"
    assert list(gen) == [1, 2, 3, "hello", b"xy", "", b"", 4, 5, 6]


def test_flatten_stream_is_lazy_on_infinite_input():
    pulled = 0

    def infinite_nested():
        nonlocal pulled
        for n in itertools.count(1):
            pulled += 1
            if pulled > 10:
                raise AssertionError("flatten_stream pulled past item 10 — not lazy!")
            yield [n, (n * 10,)]

    with cap(2, "flatten_stream materialized the whole iterable instead of yielding lazily"):
        first_six = list(itertools.islice(flatten_stream(infinite_nested()), 6))
    assert first_six == [1, 10, 2, 20, 3, 30]
    assert pulled <= 4


def test_flatten_stream_empty():
    assert list(flatten_stream([])) == []
    assert list(flatten_stream([[], [(), []]])) == []


# ---------------------------------------------------------------- window_sums

def test_window_sums_example_and_edges():
    nums = [1, 2, 3, 4, 5]
    assert window_sums(nums, 3) == [6, 9, 12]
    assert nums == [1, 2, 3, 4, 5]
    assert window_sums([1, 2, 3], 1) == [1, 2, 3]
    assert window_sums([1, 2, 3], 3) == [6]
    assert window_sums([1, 2], 3) == []
    assert window_sums([], 2) == []
    assert window_sums([-2, 5, -3, 4], 2) == [3, 2, 1]
    with pytest.raises(ValueError):
        window_sums([1, 2, 3], 0)
    with pytest.raises(ValueError):
        window_sums([1, 2, 3], -2)


def test_window_sums_random_matches_brute_force():
    import random
    rng = random.Random(1010)
    for _ in range(30):
        n = rng.randint(0, 40)
        nums = [rng.randint(-50, 50) for _ in range(n)]
        k = rng.randint(1, max(1, n + 2))
        expected = [sum(nums[i:i + k]) for i in range(n - k + 1)] if k <= n else []
        assert window_sums(nums, k) == expected


def test_window_sums_linear_time():
    # 1. Deterministic work check on a counted sequence (cross-platform, catches O(n*k) slicing!)
    class CountedSeq:
        def __init__(self, data):
            self._data = data
            self.reads = 0

        def __len__(self):
            return len(self._data)

        def __iter__(self):
            for x in self._data:
                self.reads += 1
                yield x

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                out = self._data[idx]
                self.reads += len(out)
                return out
            self.reads += 1
            return self._data[idx]

    small = CountedSeq([1] * 2_000)
    got_small = window_sums(small, 1_000)
    assert len(got_small) == 1_001 and got_small[0] == 1_000
    assert small.reads <= 6 * len(small), (
        f"window_sums made {small.reads} element reads for n={len(small)} (expected O(n), not O(n*k))"
    )

    # 2. Scale check: n = 100,000 and k = 50,000 (~2.5e9 ops if sliced!)
    n = 100_000
    k = 50_000
    nums = [1] * n
    nums[0] = 10
    nums[-1] = 20
    with cap(3, "are you recomputing sum(nums[i:i+k]) per window (O(n*k))?"):
        got = window_sums(nums, k)
    assert len(got) == n - k + 1
    assert got[0] == k + 9
    assert got[1] == k
    assert got[-1] == k + 19
