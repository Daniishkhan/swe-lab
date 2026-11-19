import random
import signal
from collections.abc import Sequence

import pytest

from monotonic import next_greater, sliding_window_max


@pytest.fixture(autouse=True)
def time_limit():
    """O(n) code finishes each test in well under a second. A nested loop
    run on a copy of the list (dodging the read counter) needs 10+ seconds
    on the big inputs, so 5 s is a generous line (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is there a loop over pairs or over every window (maybe on a copy)?")

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
            raise TooManyReads(f"over {self.budget:,} reads of a {len(self._items):,}-item list: is something O(n^2) or O(n*k)?")

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
def brute_next_greater(nums):
    out = []
    for i, x in enumerate(nums):
        out.append(next((y for y in nums[i + 1:] if y > x), -1))
    return out


def brute_window_max(nums, k):
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)] if nums else []


# 1. next_greater
def test_next_greater_examples():
    assert next_greater([2, 1, 2, 4, 3]) == [4, 2, 4, -1, -1]
    assert next_greater([5, 4, 3]) == [-1, -1, -1]
    assert next_greater([]) == []
    assert next_greater([7]) == [-1]
    assert next_greater([1, 1, 1]) == [-1, -1, -1]  # equal is not greater
    assert next_greater([2, 7, 3, 5, 4, 6, 8]) == [7, 8, 5, 6, 6, 8, -1]
    assert next_greater([-3, -1, -2]) == [-1, -1, -1]
    assert next_greater([-3, -2, -1]) == [-2, -1, -1]


def test_next_greater_matches_brute_force():
    rng = random.Random(9)
    for _ in range(400):
        nums = [rng.randint(-5, 5) for _ in range(rng.randint(0, 15))]
        assert next_greater(nums) == brute_next_greater(nums), nums


def test_next_greater_reads_each_item_about_once():
    n = 200_000
    # Mostly falling with a jump at the end: every item waits until the end,
    # so scanning right from each one reads about n^2 / 2 items.
    nums = list(range(n, 0, -1)) + [n + 1]
    got = next_greater(CountingList(nums, budget=8 * len(nums)))
    assert got == [n + 1] * n + [-1]


def test_next_greater_sawtooth():
    n = 200_000
    # 9, 8, 7, ..., 0, 19, 18, ..., 10, 29, ...: each block of 10 falls, and the
    # first item of the next block is greater than everything before it.
    nums = [10 * (i // 10) + 9 - i % 10 for i in range(n)]
    expected = [nums[(i // 10 + 1) * 10] if i // 10 + 1 < n // 10 else -1 for i in range(n)]
    assert next_greater(CountingList(nums, budget=8 * n)) == expected


# 2. sliding_window_max
def test_window_examples():
    assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_window_max([4], 1) == [4]
    assert sliding_window_max([], 3) == []
    assert sliding_window_max([9, 8, 7, 6], 2) == [9, 8, 7]
    assert sliding_window_max([1, 2, 3], 3) == [3]
    assert sliding_window_max([2, 2, 2, 2], 2) == [2, 2, 2]
    assert sliding_window_max([5, 1, 2], 1) == [5, 1, 2]


def test_window_matches_brute_force():
    rng = random.Random(21)
    for _ in range(400):
        nums = [rng.randint(-6, 6) for _ in range(rng.randint(1, 16))]
        k = rng.randint(1, len(nums))
        assert sliding_window_max(nums, k) == brute_window_max(nums, k), (nums, k)


def test_window_reads_each_item_about_once():
    n, k = 300_000, 20_000
    # Falling values: each window's max is its first item, and max() of every
    # window would read n * k = 6 billion items.
    nums = list(range(n, 0, -1))
    got = sliding_window_max(CountingList(nums, budget=8 * n), k)
    assert got == nums[: n - k + 1]


def test_window_rising_and_mountain():
    n, k = 300_000, 20_000
    rising = list(range(n))
    assert sliding_window_max(CountingList(rising, budget=8 * n), k) == list(range(k - 1, n))
    half = n // 2
    mountain = list(range(half)) + list(range(half, 0, -1))  # rises to its peak, `half`, at index half
    # On a single-peak list, a window's max is its first item, its last item,
    # or the peak if the window contains it.
    expected = [max(mountain[i], mountain[i + k - 1], half if i <= half <= i + k - 1 else 0) for i in range(n - k + 1)]
    assert sliding_window_max(CountingList(mountain, budget=8 * n), k) == expected
