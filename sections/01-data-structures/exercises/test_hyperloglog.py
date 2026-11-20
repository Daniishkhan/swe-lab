import math
import os
import random
import signal
import subprocess
import sys
import tracemalloc
from pathlib import Path

import pytest

from hyperloglog import HyperLogLog

HERE = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes a few seconds at most with O(1) adds (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 30 s: does add() do more than one hash and one register update?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def ids(n, seed, prefix="visitor"):
    rng = random.Random(seed)
    return [f"{prefix}-{i}-{rng.getrandbits(32):08x}" for i in range(n)]


def sketch(items, p=14):
    h = HyperLogLog(p)
    for x in items:
        h.add(x)
    return h


def test_example():
    # Exact unless two words share a register (well under a 1-in-500 chance with any good hash).
    h = sketch("the cat saw the other cat".split())
    assert abs(h.count() - 4) <= 1 and h.m == 16384
    assert abs(sketch("the quick brown fox jumps over the lazy dog".split()).count() - 8) <= 1


def test_empty_and_sizes():
    assert HyperLogLog().count() == 0
    for p in (4, 10, 16):
        assert HyperLogLog(p).m == 2 ** p
        assert HyperLogLog(p).count() == 0
    for p in (3, 17, 0, -1):
        with pytest.raises(ValueError):
            HyperLogLog(p)


def test_duplicates_change_nothing():
    rng = random.Random(1)
    items = ids(5_000, 2)
    once = sketch(items)
    many = HyperLogLog()
    for x in items:
        for _ in range(rng.randint(1, 5)):
            many.add(x)
    many_shuffled = sketch(rng.sample(items, len(items)) + items[:1000])
    assert many.count() == once.count() == many_shuffled.count(), "a repeated item must land in the same register with the same rho"


@pytest.mark.parametrize("n", [1, 2, 3, 10, 50, 100, 300, 1000])
def test_small_counts_use_linear_counting(n):
    got = sketch(ids(n, 100 + n)).count()
    assert abs(got - n) <= max(2, 0.025 * n), (
        f"{n} distinct items counted as {got}: below 2.5 m with empty registers, use m * ln(m / V)"
    )


@pytest.mark.parametrize("p, n", [(14, 20_000), (14, 200_000), (12, 50_000), (10, 100_000), (10, 20_000)])
def test_large_counts_within_four_standard_errors(p, n):
    got = sketch(ids(n, p * 1000 + n), p).count()
    se = 1.04 / math.sqrt(2 ** p)
    err = abs(got - n) / n
    assert err <= 4 * se, (
        f"p={p}: {n:,} distinct items counted as {got:,} ({err:.1%} off; allowed {4 * se:.1%}): "
        "check rho, alpha, and that the mean of 2 ** -register is harmonic"
    )


def test_memory_is_the_registers():
    items = ids(200_000, 3)
    tracemalloc.start()
    try:
        h = HyperLogLog(14)
        for x in items:
            h.add(x)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak <= 300_000, f"peak {peak:,} bytes: is something growing with the number of items?"
    assert abs(h.count() - 200_000) <= 0.04 * 200_000


def test_merge_is_the_union():
    a_items = ids(60_000, 4)
    b_items = a_items[40_000:] + ids(40_000, 5, "other")  # 20,000 shared, 100,000 distinct in total
    a, b = sketch(a_items), sketch(b_items)
    before = (a.count(), b.count())
    u = a.merge(b)
    assert u is not a and u is not b
    assert u.count() == sketch(a_items + b_items).count(), "merge must equal one sketch fed both streams"
    assert abs(u.count() - 100_000) <= 0.04 * 100_000
    assert (a.count(), b.count()) == before, "merge() must not modify its inputs"
    assert a.merge(a).count() == a.count()


def test_merge_needs_the_same_p():
    with pytest.raises(ValueError):
        HyperLogLog(12).merge(HyperLogLog(14))


SCRIPT = """
import sys
from hyperloglog import HyperLogLog
out = []
for s in range(5):
    h = HyperLogLog(12)
    for i in range(3000):
        h.add(f"set{s}-visitor-{i}")
    out.append(h.count())
sys.stdout.write(",".join(map(str, out)))
"""


def test_counts_are_the_same_in_every_process():
    outs = []
    for seed in ("0", "4242"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        proc = subprocess.run([sys.executable, "-c", SCRIPT], cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr
        outs.append(proc.stdout)
    assert outs[0] == outs[1], "counts depend on PYTHONHASHSEED: use hashlib, not the built-in hash()"
