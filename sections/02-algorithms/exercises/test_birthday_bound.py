import math
import signal
from fractions import Fraction

import pytest

from birthday_bound import bits_needed, collision_probability, expected_colliding_pairs


@pytest.fixture(autouse=True)
def time_limit():
    """A closed form answers in microseconds; a loop over a billion IDs takes minutes (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 2 s: for big n, use the closed form instead of multiplying n terms")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(2)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def rel_ok(got, want, rel=1e-6):
    return math.isclose(got, want, rel_tol=rel, abs_tol=0.0) or got == want


def exact_brute(n, m):
    """1 - product of (1 - i/m), in exact fractions. Only for small n."""
    if n > m:
        return Fraction(1)
    keep = Fraction(1)
    for i in range(n):
        keep *= Fraction(m - i, m)
    return 1 - keep


# Worked out offline with 60-digit decimals (exact product, or its series
# -S1/m - S2/2m^2 - S3/3m^3 when n/m is tiny).
KNOWN = [
    (23, 365, 5.07297234323985407e-1),
    (2000, 10**6, 8.64709866162082411e-1),
    (30_000, 10**9, 3.623651531470573e-1),
    (10**5, 10**9, 9.93262839088179811e-1),
    (150_000, 2**34, 4.80471560270722365e-1),    # closed form alone: 2e-6 off
    (77_163, 2**32, 4.99999890517348355e-1),
    (77_164, 2**32, 5.00008873474793442e-1),
    (300_000, 10**11, 3.623711788673117e-1),
    (10**6, 2**40, 3.65391517987193120e-1),
    (3_000_000, 10**13, 3.623717814272572e-1),
    (10**7, 10**14, 3.934693200696766e-1),
    (1000, 2**64, 2.70779492578251071e-14),
    (10**9, 2**64, 2.67410088744313590e-2),
    (5 * 10**9, 2**64, 4.92179051811252771e-1),
]


def test_expected_pairs():
    assert math.isclose(expected_colliding_pairs(23, 365), 253 / 365, rel_tol=1e-12)
    assert expected_colliding_pairs(0, 365) == 0
    assert expected_colliding_pairs(1, 365) == 0
    assert math.isclose(expected_colliding_pairs(2, 10), 0.1, rel_tol=1e-12)
    # 10^8 short links over 62^7 codes: about 1,420 colliding pairs
    assert math.isclose(expected_colliding_pairs(10**8, 62**7), 1419.8032746643717, rel_tol=1e-9)
    assert math.isclose(expected_colliding_pairs(10**12, 2**64), 27105.054312110507, rel_tol=1e-9)


def test_birthday_paradox():
    assert rel_ok(collision_probability(23, 365), 0.507297234323985)
    # The closed form alone says 0.5000, 1.4% low; the error matters at small n.
    assert abs(collision_probability(23, 365) - (1 - math.exp(-23 * 22 / 730))) > 0.005


def test_edges():
    assert collision_probability(0, 10) == 0.0
    assert collision_probability(1, 10) == 0.0
    assert collision_probability(1, 1) == 0.0
    assert collision_probability(2, 1) == 1.0
    assert collision_probability(366, 365) == 1.0
    assert collision_probability(2**32 + 1, 2**32) == 1.0       # pigeonhole, no loop
    assert rel_ok(collision_probability(2, 2), 0.5)
    assert rel_ok(collision_probability(365, 365), 1.0)


def test_against_exact_brute_force_small_m():
    for m in range(1, 41):
        for n in range(0, m + 3):
            want = float(exact_brute(n, m))
            got = collision_probability(n, m)
            assert rel_ok(got, want), f"n={n}, m={m}: got {got}, want {want}"


@pytest.mark.parametrize("n,m,want", KNOWN)
def test_known_values(n, m, want):
    got = collision_probability(n, m)
    assert rel_ok(got, want), f"n={n}, m={m}: got {got!r}, want {want!r}"


def test_tiny_probability_keeps_its_digits():
    # Multiplying (1 - i/2^64) in floats gives exactly 1.0 here, so 0.0: wrong.
    got = collision_probability(1000, 2**64)
    assert got > 0, "1 - i/2**64 rounds to 1.0 in floats; work in logs"
    assert rel_ok(got, 2.70779492578251071e-14)
    got = collision_probability(10, 2**64)
    assert rel_ok(got, 45 / 2**64)


def test_huge_n_is_fast():
    assert rel_ok(collision_probability(10**9, 2**64), 2.67410088744313590e-2)
    assert collision_probability(10**12, 2**64) == pytest.approx(1.0, abs=1e-12)
    assert rel_ok(collision_probability(10**12, 2**128), 1e24 / 2**129, rel=1e-5)


def test_bits_needed():
    assert bits_needed(0, 0.5) == 0
    assert bits_needed(1, 0.01) == 0
    assert bits_needed(2, 0.3) == 2         # 4 values: 1/4 <= 0.3
    assert bits_needed(2, 0.2) == 3         # 8 values: 1/8; 4 values: 1/4 is too much
    assert bits_needed(23, 0.5) == 9        # 365 days is not enough for 50%, 512 is
    assert bits_needed(77_164, 0.5) == 33   # 32 bits gives 0.500009
    assert bits_needed(10**5, 0.01) == 39
    assert bits_needed(10**6, 0.5) == 40
    # n^2 / 2p says 41 bits; the real 50% point needs n^2 / 2m = ln 2, so 40 do.
    assert bits_needed(1_148_500, 0.5) == 40
    assert bits_needed(10**9, 1e-6) == 79
    assert bits_needed(10**18, 1e-9) == 149
    # Inverting the closed form undercounts here: at 2**7 it says 0.2964 <= 0.3,
    # but the exact chance for 10 IDs in 128 values is 0.3027, so 8 bits are needed.
    assert bits_needed(10, 0.3) == 8
    # Same trap: 23 IDs in 512 values is 0.3944 exactly, the closed form says 0.3899.
    assert bits_needed(23, 0.392) == 10


def test_bits_needed_errors():
    for bad in [0, 1, -0.1, 1.5]:
        with pytest.raises(ValueError):
            bits_needed(100, bad)
