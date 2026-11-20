import math
import os
import random
import signal
import subprocess
import sys
import tracemalloc
from pathlib import Path

import pytest

from bloom_filter import BloomFilter

HERE = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a few seconds when add and lookup touch only k bits (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 20 s: does add or lookup touch more than k bits, or copy the whole bit array?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def words(prefix, n, seed):
    rng = random.Random(seed)
    return [f"{prefix}-{i}-{rng.getrandbits(40):x}" for i in range(n)]


def fp_rate(bf, probes):
    return sum(p in bf for p in probes) / len(probes)


def test_example():
    bf = BloomFilter(capacity=1000, error_rate=0.01)
    assert bf.num_bits == 9586 and bf.num_hashes == 7
    bf.add("apple")
    assert "apple" in bf
    assert "banana" not in bf


def test_sizes_follow_the_formulas():
    for n, p, bits, k in [(1000, 0.01, 9586, 7), (10_000, 0.001, 143_776, 10), (100, 0.1, 480, 3), (1, 0.5, 2, 1)]:
        bf = BloomFilter(n, p)
        assert bf.num_bits == bits == math.ceil(-n * math.log(p) / math.log(2) ** 2), (n, p)
        assert bf.num_hashes == k, (n, p)
        assert len(bf.to_bytes()) == (bits + 7) // 8, "to_bytes() should be ceil(num_bits / 8) bytes"


def test_bad_arguments():
    for n, p in [(0, 0.01), (-5, 0.01), (100, 0), (100, 1), (100, -0.1), (100, 1.5)]:
        with pytest.raises(ValueError):
            BloomFilter(n, p)


def test_empty_filter_says_no():
    bf = BloomFilter(100, 0.01)
    assert not any(w in bf for w in words("x", 1000, 1))
    assert bf.to_bytes() == bytes(len(bf.to_bytes()))


def test_unicode_and_empty_string():
    bf = BloomFilter(10, 0.01)
    for w in ["", "café", "日本語", "a b"]:
        bf.add(w)
    assert all(w in bf for w in ["", "café", "日本語", "a b"])


def test_no_false_negatives():
    items = words("in", 20_000, 2)
    bf = BloomFilter(20_000, 0.01)
    for w in items:
        bf.add(w)
    missing = [w for w in items if w not in bf]
    assert not missing, f"{len(missing)} added items answered 'no', e.g. {missing[:3]}: a Bloom filter never forgets"


def test_adding_twice_changes_nothing_and_lookups_do_not_write():
    bf = BloomFilter(500, 0.01)
    for w in words("a", 300, 3):
        bf.add(w)
    before = bf.to_bytes()
    for w in words("a", 300, 3):
        bf.add(w)
    for w in words("q", 2000, 4):
        _ = w in bf
    assert bf.to_bytes() == before


@pytest.mark.parametrize("n, p, probes", [(20_000, 0.01, 50_000), (10_000, 0.001, 100_000)])
def test_false_positive_rate_at_capacity(n, p, probes):
    bf = BloomFilter(n, p)
    for w in words("in", n, 5):
        bf.add(w)
    rate = fp_rate(bf, words("out", probes, 6))
    assert rate <= 1.5 * p, (
        f"false positive rate {rate:.4f} with {n:,} items, target {p}: "
        f"are all {bf.num_hashes} hash positions independent and spread over all {bf.num_bits:,} bits?"
    )


def test_over_capacity_gets_worse_not_wrong():
    bf = BloomFilter(2_000, 0.01)
    items = words("in", 8_000, 7)
    for w in items:
        bf.add(w)
    assert all(w in bf for w in items)
    assert fp_rate(bf, words("out", 20_000, 8)) > 0.1  # 4x over capacity: still no false negatives, many more false positives


def test_memory_stays_near_the_bit_array():
    n = 100_000
    items = words("m", n, 9)
    tracemalloc.start()
    try:
        bf = BloomFilter(n, 0.01)
        for w in items:
            bf.add(w)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    bits_bytes = (bf.num_bits + 7) // 8
    assert len(bf.to_bytes()) == bits_bytes
    assert peak <= 400_000, (
        f"peak {peak:,} bytes for a {bits_bytes:,}-byte bit array: "
        "are the items being stored, or the bits kept one per Python object?"
    )
    assert all(w in bf for w in items[:1000])


def test_add_and_lookup_touch_k_bits_not_the_whole_array():
    bf = BloomFilter(1_000_000, 0.01)  # about 1.2 MB of bits
    items = words("c", 200, 12)
    probes = items + words("d", 200, 13)
    tracemalloc.start()
    try:
        for w in items:
            bf.add(w)
        hits = sum(w in bf for w in probes)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert hits >= len(items)
    assert peak <= 100_000, (
        f"peak {peak:,} bytes for 200 adds and 400 lookups on a {bf.num_bits // 8:,}-byte bit array: "
        "does each add or lookup copy or rebuild the whole array (a big int, bytes + bytes, a slice)? It should touch only k bits."
    )


SCRIPT = """
import sys
from bloom_filter import BloomFilter
bf = BloomFilter(500, 0.01)
for i in range(500):
    bf.add(f"user-{i}@example.com")
sys.stdout.write(bf.to_bytes().hex())
"""


def test_bits_are_the_same_in_every_process():
    outs = []
    for seed in ("0", "12345"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        proc = subprocess.run([sys.executable, "-c", SCRIPT], cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr
        outs.append(proc.stdout)
    assert outs[0] == outs[1], "the bit array depends on PYTHONHASHSEED: use hashlib, not the built-in hash()"


def test_union_is_the_or_of_the_bits():
    a_items, b_items = words("a", 1000, 10), words("b", 1000, 11)
    a, b, both = BloomFilter(2000, 0.01), BloomFilter(2000, 0.01), BloomFilter(2000, 0.01)
    for w in a_items:
        a.add(w)
        both.add(w)
    for w in b_items:
        b.add(w)
        both.add(w)
    a_before, b_before = a.to_bytes(), b.to_bytes()
    u = a.union(b)
    assert u is not a and u is not b
    assert u.to_bytes() == bytes(x | y for x, y in zip(a_before, b_before))
    assert u.to_bytes() == both.to_bytes(), "a filter of the union should have exactly the OR of the bits"
    assert all(w in u for w in a_items + b_items)
    assert a.to_bytes() == a_before and b.to_bytes() == b_before, "union() must not modify its inputs"


def test_union_needs_matching_shapes():
    with pytest.raises(ValueError):
        BloomFilter(1000, 0.01).union(BloomFilter(2000, 0.01))
    with pytest.raises(ValueError):
        BloomFilter(1000, 0.01).union(BloomFilter(1000, 0.001))
