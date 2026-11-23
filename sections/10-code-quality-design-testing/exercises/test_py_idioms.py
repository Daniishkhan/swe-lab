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
    fns = make_multipliers([0, -1, 1])
    assert [f(9) for f in fns] == [0, -9, 9]


# ---------------------------------------------------------------- flatten_stream

def test_flatten_stream_nested_and_atomic_strings():
    data = [1, (2, [3, "hello", b"xy"]), [], [[4], (5,)]]
    gen = flatten_stream(data)
    assert iter(gen) is gen, "flatten_stream should return a lazy iterator/generator"
    assert list(gen) == [1, 2, 3, "hello", b"xy", 4, 5]


def test_flatten_stream_is_lazy_on_infinite_input():
    def infinite_nested():
        for n in itertools.count(1):
            yield [n, (n * 10,)]

    with cap(2, "flatten_stream materialized the whole iterable instead of yielding lazily"):
        first_six = list(itertools.islice(flatten_stream(infinite_nested()), 6))
    assert first_six == [1, 10, 2, 20, 3, 30]


def test_flatten_stream_empty():
    assert list(flatten_stream([])) == []
    assert list(flatten_stream([[], [(), []]])) == []


# ---------------------------------------------------------------- window_sums

def test_window_sums_example_and_edges():
    assert window_sums([1, 2, 3, 4, 5], 3) == [6, 9, 12]
    assert window_sums([1, 2, 3], 1) == [1, 2, 3]
    assert window_sums([1, 2, 3], 3) == [6]
    assert window_sums([1, 2], 3) == []
    assert window_sums([], 2) == []
    assert window_sums([-2, 5, -3, 4], 2) == [3, 2, 1]
    with pytest.raises(ValueError):
        window_sums([1, 2, 3], 0)
    with pytest.raises(ValueError):
        window_sums([1, 2, 3], -2)


def test_window_sums_linear_time():
    # n = 100,000 and k = 50,000 => ~50,000 windows of size 50,000 (~2.5e9 ops if sliced!)
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
