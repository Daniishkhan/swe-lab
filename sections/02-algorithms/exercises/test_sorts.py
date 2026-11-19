import math
import random

import pytest

from sorts import count_inversions, counting_sort, kth_smallest, merge_intervals, merge_sort, quicksort


class TooManyComparisons(AssertionError):
    pass


class Counter:
    """Counts comparisons. Gives up early past `budget`, so a slow solution fails fast instead of hanging."""

    def __init__(self, budget=5_000_000):
        self.n = 0
        self.budget = budget

    def tick(self):
        self.n += 1
        if self.n > self.budget:
            raise TooManyComparisons(f"over {self.budget:,} comparisons: something is O(n^2)")


class Item:
    """A value plus a tag. Comparisons look only at the value and are counted."""

    def __init__(self, value, tag, counter):
        self.value, self.tag, self.counter = value, tag, counter

    def _cmp(self, other):
        self.counter.tick()
        return other.value

    def __lt__(self, other): return self.value < self._cmp(other)
    def __le__(self, other): return self.value <= self._cmp(other)
    def __gt__(self, other): return self.value > self._cmp(other)
    def __ge__(self, other): return self.value >= self._cmp(other)
    def __eq__(self, other): return self.value == self._cmp(other)
    __hash__ = object.__hash__

    def __repr__(self): return f"Item({self.value}, {self.tag})"


def make(values, budget=5_000_000):
    c = Counter(budget)
    return [Item(v, i, c) for i, v in enumerate(values)], c


def values(items): return [x.value for x in items]


def is_stably_sorted(items):
    return all((a.value, a.tag) < (b.value, b.tag) for a, b in zip(items, items[1:]))


CASES = [[], [1], [2, 1], [3, 1, 2], [5, 5, 5], [4, -1, 0, 9, -1, 3, 3, 8, 2], list(range(20, 0, -1))]


# 4. merge_sort
@pytest.mark.parametrize("vals", CASES)
def test_merge_sort_examples(vals):
    items, _ = make(vals)
    before = list(items)
    out = merge_sort(items)
    assert values(out) == sorted(vals)
    assert out is not items, "return a new list, even for 0 or 1 items"
    assert [id(x) for x in items] == [id(x) for x in before], "leave the input list alone"


def test_merge_sort_stable_and_n_log_n():
    rnd = random.Random(2)
    n = 1024
    items, c = make([rnd.randint(0, 50) for _ in range(n)])
    out = merge_sort(items)
    assert is_stably_sorted(out), "equal values must keep their original order"
    limit = n * math.log2(n)
    assert c.n <= limit, f"{c.n} comparisons for n={n}, limit n log2 n = {limit:.0f}"


# 5. count_inversions
def brute_inversions(vals):
    return sum(1 for i in range(len(vals)) for j in range(i + 1, len(vals)) if vals[i] > vals[j])


@pytest.mark.parametrize("vals, expected", [
    ([], 0), ([1], 0), ([1, 2, 3], 0), ([3, 2, 1], 3), ([2, 4, 1, 3, 5], 3), ([5, 5, 5], 0), ([2, 1, 2, 1], 3),
])
def test_count_inversions_examples(vals, expected):
    items, _ = make(vals)
    assert count_inversions(items) == expected


def test_count_inversions_matches_brute_force_and_leaves_input():
    rnd = random.Random(9)
    for _ in range(100):
        vals = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 25))]
        items, _ = make(vals)
        ids = [id(x) for x in items]
        assert count_inversions(items) == brute_inversions(vals)
        assert [id(x) for x in items] == ids, "don't change the input list"


def test_count_inversions_n_log_n():
    rnd = random.Random(10)
    n = 1024
    vals = [rnd.randint(0, 10**6) for _ in range(n)]
    items, c = make(vals)
    assert count_inversions(items) == brute_inversions(vals)
    limit = n * math.log2(n)
    assert c.n <= limit, f"{c.n} comparisons for n={n}: checking every pair would be {n * (n - 1) // 2}"


# 6. quicksort
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
    items, c = make(vals, budget=int(3 * _qs_limit(n)))
    quicksort(items)
    assert values(items) == sorted(vals)
    assert c.n <= _qs_limit(n), (
        f"{c.n} comparisons on {shape} input (limit {_qs_limit(n):.0f}; n^2/2 would be {n * n // 2})")


# 7. counting_sort
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


def test_counting_sort_is_linear():
    rnd = random.Random(8)
    nums = [rnd.randint(0, 999) for _ in range(5000)]
    calls = 0

    def key(x):
        nonlocal calls
        calls += 1
        return x

    assert counting_sort(nums, key=key, max_key=999) == sorted(nums)
    assert calls <= 2 * len(nums), f"key() called {calls} times for n={len(nums)}: that's O(n * k), not O(n + k)"


# 8. merge_intervals
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


class CountedInt(int):
    """An int that counts every comparison made with it (tuple comparison uses == too)."""

    count = 0

    def _tick(self):
        CountedInt.count += 1
        if CountedInt.count > 5_000_000:
            raise TooManyComparisons("over 5,000,000 comparisons: something is O(n^2)")

    def __lt__(self, o): self._tick(); return int.__lt__(self, o)
    def __le__(self, o): self._tick(); return int.__le__(self, o)
    def __gt__(self, o): self._tick(); return int.__gt__(self, o)
    def __ge__(self, o): self._tick(); return int.__ge__(self, o)
    def __eq__(self, o): self._tick(); return int.__eq__(self, o)
    __hash__ = int.__hash__


def brute_merge(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def test_merge_intervals_n_log_n():
    rnd = random.Random(11)
    n = 2000
    raw = []
    for _ in range(n):
        s = rnd.randint(0, 10**6)
        raw.append((s, s + rnd.randint(0, 300)))
    expected = brute_merge(raw)
    CountedInt.count = 0
    got = merge_intervals([(CountedInt(s), CountedInt(e)) for s, e in raw])
    work = CountedInt.count
    assert [(int(s), int(e)) for s, e in got] == expected
    limit = 6 * n * math.log2(n)
    assert work <= limit, f"{work} comparisons for n={n} (limit {limit:.0f}): sort once, then one pass"


# 9. kth_smallest
def test_kth_smallest_examples():
    assert kth_smallest([3, 1, 2], 1) == 1
    assert kth_smallest([3, 1, 2], 3) == 3
    assert kth_smallest([5, 5, 1, 5], 2) == 5
    assert kth_smallest([7], 1) == 7


def _best_of_3(vals, k):
    """Quickselect is random: one unlucky run shouldn't fail a correct answer. Sorting never gets under ~13n."""
    want = sorted(vals)[k - 1]
    counts = []
    for _ in range(3):
        items, c = make(vals, budget=50 * len(vals))
        ids = [id(x) for x in items]
        assert kth_smallest(items, k).value == want
        assert [id(x) for x in items] == ids, "don't change the input list"
        counts.append(c.n)
    return min(counts)


@pytest.mark.parametrize("k_frac", [0.0, 0.5, 0.99])
def test_kth_smallest_linear(k_frac):
    random.seed(6)
    n = 20_000
    rnd = random.Random(7)
    vals = [rnd.randint(0, 10**9) for _ in range(n)]
    k = 1 + int(k_frac * (n - 1))
    best = _best_of_3(vals, k)
    assert best <= 10 * n, f"{best} comparisons for n={n}: about {n * math.log2(n):.0f} means you sorted everything"


@pytest.mark.parametrize("shape", ["all_equal", "few_unique"])
def test_kth_smallest_many_equal(shape):
    random.seed(12)
    n = 20_000
    rnd = random.Random(13)
    vals = [7] * n if shape == "all_equal" else [rnd.randint(0, 3) for _ in range(n)]
    best = _best_of_3(vals, n // 2)
    assert best <= 10 * n, f"{best} comparisons on {shape} input: equal items need a three-way partition"
