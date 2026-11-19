import random
import signal
from collections import Counter
from collections.abc import Sequence

import pytest

from hash_patterns import group_anagrams, subarray_sum_count, two_sum


@pytest.fixture(autouse=True)
def time_limit():
    """An O(n) answer runs each test in well under 0.1 s. An O(n^2) one that
    dodges the read counter (by working on a copy or a derived list) takes
    10+ s on the big inputs, so 5 s is a generous line (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is there a loop over pairs (maybe on a copy or a prefix-sum list)?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class TooManyReads(AssertionError):
    pass


class CountingList(Sequence):
    """A read-only list that counts reads and gives up past a budget."""

    def __init__(self, items, budget):
        self._items = list(items)
        self.reads = 0
        self.budget = budget

    def _tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooManyReads(f"over {self.budget:,} reads of a {len(self._items):,}-item list: is something O(n^2)?")

    def __getitem__(self, i):
        if isinstance(i, slice):
            out = self._items[i]
            self._tick(len(out))
            return out
        self._tick()
        return self._items[i]

    def __iter__(self):
        for x in self._items:
            self._tick()
            yield x

    def __len__(self):
        return len(self._items)


# Brute forces: slow on purpose, used only to check answers on small inputs.
def brute_two_sum(nums, target):
    for j in range(len(nums)):
        for i in range(j):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None


def brute_subarrays(nums, k):
    return sum(sum(nums[i:j]) == k for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))


def as_pair(x):
    return None if x is None else tuple(x)


# 1. two_sum
def test_two_sum_examples():
    assert as_pair(two_sum([2, 7, 11, 15], 9)) == (0, 1)
    assert as_pair(two_sum([3, 3], 6)) == (0, 1)
    assert as_pair(two_sum([3, 2, 4], 6)) == (1, 2)
    assert two_sum([1, 2, 3], 100) is None
    assert two_sum([], 0) is None
    assert two_sum([5], 10) is None


def test_two_sum_does_not_use_an_item_twice():
    assert two_sum([5, 1], 10) is None


def test_two_sum_negatives_and_choice():
    assert as_pair(two_sum([-3, 4, 3, 90], 0)) == (0, 2)
    assert as_pair(two_sum([1, 4, 2, 3, 0, 5], 7)) == (1, 3)  # (1, 3) and (2, 5) both work: smallest j wins
    assert as_pair(two_sum([2, 2, 2], 4)) == (0, 1)  # smallest i for that j


def test_two_sum_matches_brute_force():
    rng = random.Random(7)
    for _ in range(300):
        nums = [rng.randint(-10, 10) for _ in range(rng.randint(0, 12))]
        t = rng.randint(-15, 15)
        assert as_pair(two_sum(nums, t)) == brute_two_sum(nums, t), (nums, t)


def test_two_sum_reads_each_item_about_once():
    n = 20_000
    nums = CountingList(range(n), budget=3 * n)
    assert as_pair(two_sum(nums, 2 * n - 3)) == (n - 2, n - 1)  # the pair is at the very end


# 2. group_anagrams
def test_group_anagrams_example():
    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]


def test_group_anagrams_edges():
    assert group_anagrams([]) == []
    assert group_anagrams([""]) == [[""]]
    assert group_anagrams(["a", "a"]) == [["a", "a"]]
    # Same letters, different counts: not anagrams.
    assert group_anagrams(["ab", "ba", "abb", "bab", "aab"]) == [["ab", "ba"], ["abb", "bab"], ["aab"]]


def test_group_anagrams_reads_each_word_about_once():
    rng = random.Random(3)
    n = 40_000
    # 8 random letters: almost every word is its own group, so scanning a list
    # of groups for each word is O(n^2).
    words = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8)) for _ in range(n)]
    groups = group_anagrams(CountingList(words, budget=3 * n))
    assert sorted(w for g in groups for w in g) == sorted(words)
    labels = [frozenset(Counter(g[0]).items()) for g in groups]
    assert len(labels) == len(set(labels)), "two groups hold anagrams of each other"
    for g in groups:
        assert len({"".join(sorted(w)) for w in g}) == 1, "a group mixes words that aren't anagrams"


# 3. subarray_sum_count
def test_subarray_examples():
    assert subarray_sum_count([1, 1, 1], 2) == 2
    assert subarray_sum_count([1, 2, 3], 3) == 2
    assert subarray_sum_count([1, -1, 1, -1], 0) == 4
    assert subarray_sum_count([], 0) == 0
    assert subarray_sum_count([0, 0, 0], 0) == 6
    assert subarray_sum_count([5], 5) == 1


def test_subarray_matches_brute_force():
    rng = random.Random(11)
    for _ in range(300):
        nums = [rng.randint(-3, 3) for _ in range(rng.randint(0, 14))]
        k = rng.randint(-4, 4)
        assert subarray_sum_count(nums, k) == brute_subarrays(nums, k), (nums, k)


def test_subarray_reads_each_item_about_once():
    rng = random.Random(5)
    n = 20_000
    nums = [rng.randint(-5, 5) for _ in range(n)]
    # 737,692 was computed once, offline, with an O(n^2) count over every (i, j).
    assert subarray_sum_count(CountingList(nums, budget=3 * n), 3) == 737_692
