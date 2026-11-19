import math
import random
import time

import pytest

from complexity_drills import DynamicArray, count_pairs_with_sum, fast_power, has_duplicate


# 1. has_duplicate
def test_has_duplicate_small():
    assert has_duplicate([3, 1, 4, 1]) is True
    assert has_duplicate([3, 1, 4]) is False
    assert has_duplicate([]) is False
    assert has_duplicate(["a", "b", "a"]) is True


def test_has_duplicate_is_linear():
    n = 20_000
    nums = list(range(n))  # no duplicates: the worst case, every item is checked
    start = time.perf_counter()
    assert has_duplicate(nums) is False
    elapsed = time.perf_counter() - start
    # O(n) runs in well under a second; comparing all 200 million pairs takes 10+ seconds.
    assert elapsed < 1.0, f"took {elapsed:.1f}s: is something O(n^2)?"


# 2. DynamicArray
def test_dynamic_array_basics():
    a = DynamicArray()
    assert len(a) == 0
    for i in range(10):
        a.append(i * i)
    assert len(a) == 10
    assert [a[i] for i in range(10)] == [i * i for i in range(10)]
    assert a.capacity >= 10


def test_dynamic_array_index_errors():
    a = DynamicArray()
    a.append("x")
    with pytest.raises(IndexError):
        a[1]


def test_dynamic_array_grows_by_doubling():
    a = DynamicArray()
    caps = set()
    for i in range(100):
        a.append(i)
        caps.add(a.capacity)
    assert caps <= {1, 2, 4, 8, 16, 32, 64, 128}


def test_dynamic_array_amortized_copies():
    n = 100_000
    a = DynamicArray()
    for i in range(n):
        a.append(i)
    assert a[n - 1] == n - 1
    assert 0 < a.copies < 2 * n, f"{a.copies} copies for {n} appends: not amortized O(1)"


# 3. count_pairs_with_sum
class CountingList:
    """A read-only list that counts how many times it's read."""

    def __init__(self, data):
        self._data = list(data)
        self.reads = 0

    def __len__(self):
        return len(self._data)

    def __getitem__(self, i):
        if isinstance(i, slice):
            raise TypeError("no slicing: slicing copies, and copies hide work")
        self.reads += 1
        return self._data[i]

    def __iter__(self):
        for x in self._data:
            self.reads += 1
            yield x


def brute_pairs(nums, target):
    return sum(1 for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == target)


def test_count_pairs_examples():
    assert count_pairs_with_sum([1, 2, 3, 4, 5, 6], 7) == 3
    assert count_pairs_with_sum([1, 2, 3], 100) == 0
    assert count_pairs_with_sum([], 5) == 0
    assert count_pairs_with_sum([-3, -1, 0, 2, 4], 1) == 2


def test_count_pairs_matches_brute_force():
    rng = random.Random(3)
    for _ in range(100):
        nums = sorted(rng.sample(range(-50, 50), rng.randint(0, 20)))
        t = rng.randint(-60, 60)
        assert count_pairs_with_sum(nums, t) == brute_pairs(nums, t)


def test_count_pairs_reads_linear():
    n = 2000
    data = CountingList(range(0, 2 * n, 2))  # 0, 2, 4, ...
    count_pairs_with_sum(data, 2 * n)
    assert data.reads <= 2 * n + 10, f"{data.reads} reads for n={n}: a nested loop would be ~{n * n // 2}"


# 4. fast_power
def test_fast_power_values():
    assert fast_power(2, 10)[0] == 1024
    assert fast_power(3, 0)[0] == 1
    assert fast_power(7, 1)[0] == 7
    assert fast_power(5, 13)[0] == 5 ** 13


@pytest.mark.parametrize("exp", [1, 2, 15, 16, 1000, 1_000_000])
def test_fast_power_logarithmic(exp):
    result, mults = fast_power(1, exp)
    assert result == 1
    assert mults <= 2 * math.log2(exp) + 2, f"{mults} multiplications for exp={exp}"
