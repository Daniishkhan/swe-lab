import random
import signal

import pytest

from jump_hash import jump_hash


@pytest.fixture(autouse=True)
def time_limit():
    """The log-time loop finishes all of these in well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: are you visiting every bucket count instead of jumping?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# (key, num_buckets, bucket), computed offline with the paper's C++ code.
KNOWN = [
    (0, 1, 0),
    (0, 10, 0),
    (1, 10, 6),
    (12345, 7, 1),
    (18446744073709551615, 1000, 313),
    (256, 1024, 520),
    (10771459963163966554, 2, 0),
    (16897640540126481569, 3, 1),
    (3802588160415712676, 10, 8),
    (12759209388486921995, 100, 53),
    (11249233829017174838, 1000, 105),
    (8202813829041183804, 65536, 51955),
    (3793178537892732345, 1000000, 107982),
    (1705883262593361569, 2147483647, 103468500),
]


@pytest.mark.parametrize("key,n,want", KNOWN)
def test_known_values(key, n, want):
    assert jump_hash(key, n) == want


def test_one_bucket_and_bad_counts():
    assert all(jump_hash(k, 1) == 0 for k in range(100))
    with pytest.raises(ValueError):
        jump_hash(5, 0)
    with pytest.raises(ValueError):
        jump_hash(5, -3)


def test_always_in_range():
    rng = random.Random(1)
    for _ in range(2000):
        n = rng.randint(1, 500)
        assert 0 <= jump_hash(rng.randrange(2**64), n) < n


def test_growing_moves_keys_only_into_the_new_bucket():
    rng = random.Random(2)
    keys = [rng.randrange(2**64) for _ in range(3000)]
    for n in (1, 2, 5, 9, 31, 99):
        moved = 0
        for k in keys:
            a, b = jump_hash(k, n), jump_hash(k, n + 1)
            assert b == a or b == n, f"key {k} moved from bucket {a} to {b} when going from {n} to {n + 1} buckets"
            moved += b != a
        expected = len(keys) / (n + 1)
        assert 0.75 * expected < moved < 1.25 * expected, (n, moved, expected)


def test_even_spread():
    rng = random.Random(3)
    counts = [0] * 10
    for _ in range(10000):
        counts[jump_hash(rng.randrange(2**64), 10)] += 1
    assert max(counts) < 1100 and min(counts) > 900, counts


def test_sequential_keys_spread_too():
    counts = [0] * 8
    for k in range(8000):
        counts[jump_hash(k, 8)] += 1
    assert max(counts) < 1150 and min(counts) > 850, counts


def test_huge_bucket_counts_are_fast():
    rng = random.Random(4)
    n = 2**31 - 1
    for _ in range(2000):
        assert 0 <= jump_hash(rng.randrange(2**64), n) < n
