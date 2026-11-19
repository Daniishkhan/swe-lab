import bisect
import random

from binary_search import lower_bound, min_ship_capacity


def test_lower_bound_examples():
    assert lower_bound([1, 3, 3, 5], 3) == 1
    assert lower_bound([1, 3, 3, 5], 4) == 3
    assert lower_bound([1, 3, 3, 5], 0) == 0
    assert lower_bound([1, 3, 3, 5], 9) == 4
    assert lower_bound([], 1) == 0


def test_lower_bound_matches_bisect():
    rng = random.Random(1)
    for _ in range(300):
        nums = sorted(rng.randint(0, 20) for _ in range(rng.randint(0, 15)))
        t = rng.randint(-2, 22)
        assert lower_bound(nums, t) == bisect.bisect_left(nums, t)


def test_min_ship_capacity():
    assert min_ship_capacity([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15
    assert min_ship_capacity([3, 2, 2, 4, 1, 4], 3) == 6
    assert min_ship_capacity([1, 2, 3, 1, 1], 4) == 3
    assert min_ship_capacity([10], 1) == 10
