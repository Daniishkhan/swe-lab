import math
import random

import pytest

from sorts import counting_sort, insertion_sort, kth_smallest, merge_intervals, merge_sort, quicksort


class Counter:
    def __init__(self):
        self.n = 0


class Item:
    """A value plus a tag. Comparisons look only at the value and are counted."""

    def __init__(self, value, tag, counter):
        self.value, self.tag, self.counter = value, tag, counter

    def _cmp(self, other):
        self.counter.n += 1
        return other.value

    def __lt__(self, other): return self.value < self._cmp(other)
    def __le__(self, other): return self.value <= self._cmp(other)
    def __gt__(self, other): return self.value > self._cmp(other)
    def __ge__(self, other): return self.value >= self._cmp(other)
    def __eq__(self, other): return self.value == self._cmp(other)
    __hash__ = object.__hash__

    def __repr__(self): return f"Item({self.value}, {self.tag})"


def make(values):
    c = Counter()
    return [Item(v, i, c) for i, v in enumerate(values)], c


def values(items): return [x.value for x in items]


def is_stably_sorted(items):
    return all((a.value, a.tag) < (b.value, b.tag) for a, b in zip(items, items[1:]))


CASES = [[], [1], [2, 1], [3, 1, 2], [5, 5, 5], [4, -1, 0, 9, -1, 3, 3, 8, 2], list(range(20, 0, -1))]


# 1. insertion_sort
@pytest.mark.parametrize("vals", CASES)
def test_insertion_sort_examples(vals):
    items, _ = make(vals)
    insertion_sort(items)
    assert values(items) == sorted(vals)


def test_insertion_sort_stable_random():
    rnd = random.Random(1)
    items, _ = make([rnd.randint(0, 9) for _ in range(300)])
    insertion_sort(items)
    assert is_stably_sorted(items), "equal values must keep their original order"


def test_insertion_sort_fast_on_nearly_sorted():
    n = 2000
    vals = list(range(n))
    for i in (10, 500, 1200, 1800, 1990):  # five neighbors swapped
        vals[i], vals[i + 1] = vals[i + 1], vals[i]
    items, c = make(vals)
    insertion_sort(items)
    assert values(items) == list(range(n))
    assert c.n <= 3 * n, f"{c.n} comparisons on a nearly sorted list of {n}: should be about n"


# 2. merge_sort
@pytest.mark.parametrize("vals", CASES)
def test_merge_sort_examples(vals):
    items, _ = make(vals)
    before = list(items)
    out = merge_sort(items)
    assert values(out) == sorted(vals)
    assert items == before, "merge_sort must return a new list and leave the input alone"


def test_merge_sort_stable_and_n_log_n():
    rnd = random.Random(2)
    n = 1024
    items, c = make([rnd.randint(0, 50) for _ in range(n)])
    out = merge_sort(items)
    assert is_stably_sorted(out), "equal values must keep their original order"
    limit = n * math.log2(n)
    assert c.n <= limit, f"{c.n} comparisons for n={n}, limit n log2 n = {limit:.0f}"


# 3. quicksort
@pytest.mark.parametrize("vals", CASES)
def test_quicksort_examples(vals):
    items, _ = make(vals)
    quicksort(items)
    assert values(items) == sorted(vals)


def _qs_limit(n): return 4 * n * math.log2(n)


@pytest.mark.parametrize("shape", ["random", "sorted", "reversed", "all_equal", "few_unique"])
def test_quicksort_stays_n_log_n(shape):
    random.seed(3)
    n = 3000
    rnd = random.Random(4)
    vals = {
        "random": [rnd.randint(0, 10**6) for _ in range(n)],
        "sorted": list(range(n)),
        "reversed": list(range(n, 0, -1)),
        "all_equal": [7] * n,
        "few_unique": [rnd.randint(0, 3) for _ in range(n)],
    }[shape]
    items, c = make(vals)
    quicksort(items)
    assert values(items) == sorted(vals)
    assert c.n <= _qs_limit(n), (
        f"{c.n} comparisons on {shape} input (limit {_qs_limit(n):.0f}; n^2/2 would be {n * n // 2})")


# 4. counting_sort
class NoCompare:
    def __init__(self, age, name): self.age, self.name = age, name
    def _no(self, other): raise TypeError("counting sort never compares items")
    __lt__ = __le__ = __gt__ = __ge__ = _no


def test_counting_sort_stable_without_comparisons():
    people = [NoCompare(a, n) for a, n in [(30, "ana"), (25, "bo"), (30, "cy"), (0, "di"), (25, "ed"), (99, "fay")]]
    out = counting_sort(people, key=lambda p: p.age, max_key=99)
    assert [p.name for p in out] == ["di", "bo", "ed", "ana", "cy", "fay"]
    assert [p.name for p in people] == ["ana", "bo", "cy", "di", "ed", "fay"], "return a new list"


def test_counting_sort_edges():
    assert counting_sort([], key=lambda x: x, max_key=5) == []
    rnd = random.Random(5)
    nums = [rnd.randint(0, 255) for _ in range(5000)]
    assert counting_sort(nums, key=lambda x: x, max_key=255) == sorted(nums)


# 5. merge_intervals
@pytest.mark.parametrize("given, expected", [
    ([], []),
    ([(1, 3), (2, 6), (8, 10), (15, 18)], [(1, 6), (8, 10), (15, 18)]),
    ([(8, 10), (1, 3), (2, 6)], [(1, 6), (8, 10)]),
    ([(1, 4), (4, 5)], [(1, 5)]),
    ([(1, 10), (2, 3), (4, 5)], [(1, 10)]),
    ([(5, 5)], [(5, 5)]),
])
def test_merge_intervals(given, expected):
    assert [tuple(x) for x in merge_intervals(given)] == expected


# 6. kth_smallest
def test_kth_smallest_examples():
    assert kth_smallest([3, 1, 2], 1) == 1
    assert kth_smallest([3, 1, 2], 3) == 3
    assert kth_smallest([5, 5, 1, 5], 2) == 5
    assert kth_smallest([7], 1) == 7


@pytest.mark.parametrize("k_frac", [0.0, 0.5, 0.99])
def test_kth_smallest_linear(k_frac):
    random.seed(6)
    n = 20_000
    rnd = random.Random(7)
    vals = [rnd.randint(0, 10**9) for _ in range(n)]
    k = 1 + int(k_frac * (n - 1))
    items, c = make(vals)
    assert kth_smallest(items, k).value == sorted(vals)[k - 1]
    assert c.n <= 10 * n, f"{c.n} comparisons for n={n}: about {n * math.log2(n):.0f} means you sorted everything"
