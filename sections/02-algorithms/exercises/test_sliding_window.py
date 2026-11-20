import random
import tracemalloc
from itertools import groupby

import pytest

from sliding_window import (
    anagram_starts,
    count_pairs_at_most,
    count_sum_k,
    dedupe_sorted,
    longest_k_distinct,
    shortest_reaching,
)


class TooMuchWork(AssertionError):
    pass


# ---------------------------------------------------------------------------
# Work-counting inputs
# ---------------------------------------------------------------------------
class Text:
    """A read-only string that counts every character read. Fails fast past `budget`."""

    def __init__(self, s, budget=10**9):
        self._s, self.reads, self.budget = s, 0, budget

    def _tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooMuchWork(f"over {self.budget:,} character reads: something re-reads the same characters")

    def __len__(self):
        return len(self._s)

    def __getitem__(self, i):
        out = self._s[i]
        self._tick(len(out) if isinstance(i, slice) else 1)
        return out

    def __iter__(self):
        for ch in self._s:
            self._tick()
            yield ch


class Num:
    """A number that counts every + and - and every comparison done with it.

    The result of + or - is a Num too, so running totals and prefix sums you
    build from the inputs are counted as well: copying can't hide the work.
    """

    ops = cmps = 0
    budget = cmp_budget = 10**9

    def __init__(self, v):
        self.v = v

    @classmethod
    def reset(cls, budget, cmp_budget):
        cls.ops, cls.budget, cls.cmps, cls.cmp_budget = 0, budget, 0, cmp_budget

    @staticmethod
    def _raw(o):
        return o.v if isinstance(o, Num) else o

    @staticmethod
    def _tick():
        Num.ops += 1
        if Num.ops > Num.budget:
            raise TooMuchWork(f"over {Num.budget:,} additions/subtractions: something adds up the same numbers again")

    def _cmp(self, o):
        Num.cmps += 1
        if Num.cmps > Num.cmp_budget:
            raise TooMuchWork(f"over {Num.cmp_budget:,} comparisons: something compares the same pairs over and over")
        return self._raw(o)

    def __add__(self, o): self._tick(); return Num(self.v + self._raw(o))
    __radd__ = __add__
    def __sub__(self, o): self._tick(); return Num(self.v - self._raw(o))
    def __rsub__(self, o): self._tick(); return Num(self._raw(o) - self.v)
    def __neg__(self): self._tick(); return Num(-self.v)
    def __lt__(self, o): return self.v < self._cmp(o)
    def __le__(self, o): return self.v <= self._cmp(o)
    def __gt__(self, o): return self.v > self._cmp(o)
    def __ge__(self, o): return self.v >= self._cmp(o)
    def __eq__(self, o): return self.v == self._cmp(o)
    def __bool__(self): return self.v != 0
    def __hash__(self): return hash(self.v)
    def __repr__(self): return f"Num({self.v})"


def nums_of(values, budget):
    """Fresh counters. budget caps + and -; comparisons get 40 per item, enough for a sort."""
    Num.reset(budget, cmp_budget=40 * len(values) + 10)
    return [Num(v) for v in values]


class Tape:
    """A fixed-size array: read and write by index, nothing else. Counts reads and writes."""

    def __init__(self, data, budget=10**9):
        self._a, self.reads, self.writes, self.budget = list(data), 0, 0, budget

    def _check(self, i):
        if isinstance(i, slice):
            raise TypeError("no slicing: a slice is a copy, and in place means no copies")

    def __len__(self):
        return len(self._a)

    def __getitem__(self, i):
        self._check(i)
        self.reads += 1
        if self.reads > self.budget:
            raise TooMuchWork(f"over {self.budget:,} reads")
        return self._a[i]

    def __setitem__(self, i, v):
        self._check(i)
        self.writes += 1
        if self.writes > self.budget:
            raise TooMuchWork(f"over {self.budget:,} writes: shifting items over and over is O(n^2)")
        self._a[i] = v


# ---------------------------------------------------------------------------
# Brute forces (slow but obviously right)
# ---------------------------------------------------------------------------
def brute_pairs(nums, limit):
    return sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] <= limit)


def brute_dedupe(nums, keep):
    return [v for _, g in groupby(nums) for v in list(g)[:keep]]


def brute_anagrams(text, pattern):
    m, want = len(pattern), sorted(pattern)
    return [i for i in range(len(text) - m + 1) if sorted(text[i:i + m]) == want]


def brute_longest(s, k):
    return max([j - i for i in range(len(s)) for j in range(i, len(s) + 1) if len(set(s[i:j])) <= k], default=0)


def brute_shortest(nums, target):
    best = 0
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            if sum(nums[i:j + 1]) >= target:
                if best == 0 or j - i + 1 < best:
                    best = j - i + 1
                break
    return best


def brute_sum_k(nums, k):
    return sum(1 for i in range(len(nums)) for j in range(i, len(nums)) if sum(nums[i:j + 1]) == k)


# ---------------------------------------------------------------------------
# 4. count_pairs_at_most
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nums, limit, expected", [
    ([3, 1, 5, 2], 6, 4),
    ([], 10, 0),
    ([5], 10, 0),
    ([1, 1], 2, 1),
    ([1, 1], 1, 0),
    ([2, 2, 2, 2], 4, 6),
    ([-3, 7, 0, -1, 4], 3, 5),
    ([10, 20, 30], 5, 0),
])
def test_count_pairs_examples(nums, limit, expected):
    before = list(nums)
    assert count_pairs_at_most(nums, limit) == expected
    assert nums == before, "don't change the input list (sort a copy)"


def test_count_pairs_matches_brute_force():
    rnd = random.Random(41)
    for _ in range(300):
        nums = [rnd.randint(-10, 10) for _ in range(rnd.randint(0, 14))]
        limit = rnd.randint(-15, 15)
        assert count_pairs_at_most(nums, limit) == brute_pairs(nums, limit), (nums, limit)


@pytest.mark.parametrize("shape", ["random", "all_equal"])
def test_count_pairs_linear_additions(shape):
    rnd = random.Random(42)
    n = 2000
    values = [rnd.randint(-1000, 1000) for _ in range(n)] if shape == "random" else [3] * n
    limit = 0 if shape == "random" else 6  # about half of all pairs pass, or every pair does
    expected = brute_pairs(values, limit)
    nums = nums_of(values, budget=3 * n)
    assert count_pairs_at_most(nums, limit) == expected
    # Over budget raises inside your code. Checking every pair is about n^2 / 2 = 2,000,000 additions.
    assert Num.ops <= 3 * n


# ---------------------------------------------------------------------------
# 5. dedupe_sorted
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nums, keep, expected", [
    ([1, 1, 1, 2, 2, 3], 2, [1, 1, 2, 2, 3]),
    ([1, 1, 1, 2, 2, 3], 1, [1, 2, 3]),
    ([], 1, []),
    ([7], 1, [7]),
    ([7], 3, [7]),
    ([4, 4, 4, 4], 1, [4]),
    ([4, 4, 4, 4], 3, [4, 4, 4]),
    ([1, 2, 3], 1, [1, 2, 3]),
    ([-2, -2, 0, 0, 0, 5, 5, 5, 5, 9], 2, [-2, -2, 0, 0, 5, 5, 9]),
])
def test_dedupe_examples(nums, keep, expected):
    arr = list(nums)
    k = dedupe_sorted(arr, keep)
    assert isinstance(k, int)
    assert arr[:k] == expected
    assert len(arr) == len(nums), "in place: overwrite slots, don't delete them"


def test_dedupe_matches_brute_force():
    rnd = random.Random(51)
    for _ in range(300):
        nums = sorted(rnd.randint(0, 6) for _ in range(rnd.randint(0, 20)))
        keep = rnd.randint(1, 4)
        tape = Tape(nums)
        k = dedupe_sorted(tape, keep)
        assert tape._a[:k] == brute_dedupe(nums, keep), (nums, keep)


def test_dedupe_linear_reads_and_writes():
    rnd = random.Random(52)
    n = 100_000
    nums = sorted(rnd.randint(0, n // 20) for _ in range(n))  # about 20 copies of each value
    expected = brute_dedupe(nums, 2)
    tape = Tape(nums, budget=4 * n + 10)
    k = dedupe_sorted(tape, 2)
    assert tape._a[:k] == expected
    assert tape.writes <= n, f"{tape.writes} writes for n={n}: each kept item needs at most one write"


def test_dedupe_constant_extra_memory():
    rnd = random.Random(53)
    n = 100_000
    nums = sorted(rnd.randint(0, n // 3) for _ in range(n))
    tape = Tape(nums, budget=4 * n + 10)
    tracemalloc.start()
    try:
        start = tracemalloc.get_traced_memory()[0]
        tracemalloc.reset_peak()
        k = dedupe_sorted(tape, 1)
        extra = tracemalloc.get_traced_memory()[1] - start
    finally:
        tracemalloc.stop()
    assert tape._a[:k] == sorted(set(nums))
    # A copy of 100,000 items costs about 800,000 bytes; a set or dict of them, several MB.
    assert extra < 100_000, f"used {extra:,} extra bytes: that's a copy of the data, not in place"


# ---------------------------------------------------------------------------
# 6. anagram_starts
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text, pattern, expected", [
    ("cbaebabacd", "abc", [0, 6]),
    ("abab", "ab", [0, 1, 2]),
    ("", "a", []),
    ("a", "a", [0]),
    ("a", "b", []),
    ("ab", "abc", []),
    ("aaaa", "aa", [0, 1, 2]),
    ("baa", "aab", [0]),
    ("abcabc", "abcabc", [0]),
])
def test_anagram_examples(text, pattern, expected):
    assert list(anagram_starts(text, pattern)) == expected


def test_anagram_matches_brute_force():
    rnd = random.Random(61)
    for _ in range(300):
        text = "".join(rnd.choice("abc") for _ in range(rnd.randint(0, 25)))
        pattern = "".join(rnd.choice("abc") for _ in range(rnd.randint(1, 5)))
        assert list(anagram_starts(text, pattern)) == brute_anagrams(text, pattern), (text, pattern)


def test_anagram_linear_reads():
    rnd = random.Random(62)
    n, m = 20_000, 100
    raw = "".join(rnd.choice("ab") for _ in range(n))
    pat = raw[5000:5000 + m][::-1]  # guarantees at least one match
    expected = brute_anagrams(raw, pat)
    text, pattern = Text(raw, budget=5 * n + 10), Text(pat, budget=5 * m + 10)
    assert list(anagram_starts(text, pattern)) == expected
    # Over budget raises inside your code. Checking every window from scratch reads about n * m = 2,000,000.
    assert text.reads <= 5 * n + 10


# ---------------------------------------------------------------------------
# 7. longest_k_distinct
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("s, k, expected", [
    ("eceba", 2, 3),
    ("aa", 1, 2),
    ("", 2, 0),
    ("a", 0, 0),
    ("abc", 0, 0),
    ("a", 1, 1),
    ("abc", 5, 3),
    ("abaccc", 2, 4),
    ("aabbcc", 1, 2),
])
def test_longest_examples(s, k, expected):
    assert longest_k_distinct(s, k) == expected


def test_longest_matches_brute_force():
    rnd = random.Random(71)
    for _ in range(300):
        s = "".join(rnd.choice("abcd") for _ in range(rnd.randint(0, 20)))
        k = rnd.randint(0, 4)
        assert longest_k_distinct(s, k) == brute_longest(s, k), (s, k)


@pytest.mark.parametrize("alphabet, k", [("abc", 3), ("aaaaaaab", 1), ("abcdef", 2)])
def test_longest_linear_reads(alphabet, k):
    rnd = random.Random(72)
    n = 6000
    raw = "".join(rnd.choice(alphabet) for _ in range(n))
    s = Text(raw, budget=6 * n + 10)
    got = longest_k_distinct(s, k)
    if alphabet == "abc":
        assert got == n
    else:
        assert got == longest_k_distinct(raw, k)
    # Over budget raises inside your code. Trying every start reads about n^2 / 2 = 18,000,000 characters.
    assert s.reads <= 6 * n + 10


# ---------------------------------------------------------------------------
# 8. shortest_reaching
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nums, target, expected", [
    ([2, 3, 1, 2, 4, 3], 7, 2),
    ([1, 4, 4], 4, 1),
    ([1, 1, 1, 1, 1, 1, 1, 1], 11, 0),
    ([], 1, 0),
    ([5], 5, 1),
    ([5], 6, 0),
    ([1, 2, 3, 4, 5], 15, 5),
    ([3, 3, 3, 3], 6, 2),
    ([1, 1, 9, 1, 1], 9, 1),
])
def test_shortest_examples(nums, target, expected):
    assert shortest_reaching(nums, target) == expected


def test_shortest_matches_brute_force():
    rnd = random.Random(81)
    for _ in range(300):
        nums = [rnd.randint(1, 9) for _ in range(rnd.randint(0, 15))]
        target = rnd.randint(1, 40)
        assert shortest_reaching(nums, target) == brute_shortest(nums, target), (nums, target)


@pytest.mark.parametrize("case", ["long_window", "no_answer"])
def test_shortest_linear_additions(case):
    rnd = random.Random(82)
    n = 5000
    values = [rnd.randint(1, 100) for _ in range(n)]
    target = sum(values) // 2 if case == "long_window" else sum(values) + 1
    expected = shortest_reaching(values, target) if case == "long_window" else 0  # correctness: tests above
    nums = nums_of(values, budget=3 * n)
    assert shortest_reaching(nums, target) == expected
    # Over budget raises inside your code. Restarting the sum at every start is about n^2 / 4 additions or more.
    assert Num.ops <= 3 * n


# ---------------------------------------------------------------------------
# 9. count_sum_k
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nums, k, expected", [
    ([1, 1, 1], 2, 2),
    ([1, 2, 3], 3, 2),
    ([1, -1, 0], 0, 3),
    ([], 0, 0),
    ([5], 5, 1),
    ([5], 0, 0),
    ([0, 0, 0], 0, 6),
    ([3, 4, 7, 2, -3, 1, 4, 2], 7, 4),
    ([-1, -1, 1], 0, 1),
])
def test_sum_k_examples(nums, k, expected):
    assert count_sum_k(nums, k) == expected


def test_sum_k_matches_brute_force():
    rnd = random.Random(91)
    for _ in range(300):
        nums = [rnd.randint(-4, 4) for _ in range(rnd.randint(0, 15))]
        k = rnd.randint(-5, 5)
        assert count_sum_k(nums, k) == brute_sum_k(nums, k), (nums, k)


def test_sum_k_linear_additions():
    rnd = random.Random(92)
    n = 4000
    values = [rnd.randint(-5, 5) for _ in range(n)]
    expected = count_sum_k(values, 3)  # correctness is checked above; this test measures work
    nums = nums_of(values, budget=3 * n)
    assert count_sum_k(nums, 3) == expected
    # Over budget raises inside your code. Every (start, end) pair is about n^2 / 2 = 8,000,000 additions.
    assert Num.ops <= 3 * n
