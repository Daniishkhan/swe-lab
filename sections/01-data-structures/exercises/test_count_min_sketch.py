import math
import os
import random
import signal
import subprocess
import sys
import tracemalloc
from collections import Counter
from pathlib import Path

import pytest

from count_min_sketch import CountMinSketch, heavy_hitters

HERE = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes a few seconds at most with O(depth) updates (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 30 s: does each add or estimate do more than one hash per row?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def skewed_stream(n_items, total, seed):
    """A Zipf-like stream: item i appears about proportionally to 1 / (i + 1)."""
    rng = random.Random(seed)
    names = [f"ip-{i}-{rng.getrandbits(32):08x}" for i in range(n_items)]
    weights = [1 / (i + 1) for i in range(n_items)]
    stream = rng.choices(names, weights, k=total)
    return names, stream


def test_example():
    cms = CountMinSketch(epsilon=0.01, delta=0.01)
    assert (cms.width, cms.depth) == (272, 5)
    for word in "to be or not to be".split():
        cms.add(word)
    assert cms.estimate("to") == 2 and cms.estimate("be") == 2 and cms.estimate("or") == 1
    assert cms.estimate("hamlet") == 0
    assert cms.total == 6


def test_sizes_follow_the_formulas():
    for eps, delta, w, d in [(0.001, 0.01, 2719, 5), (0.01, 0.05, 272, 3), (0.1, 0.5, 28, 1), (1e-4, 0.001, 27183, 7)]:
        cms = CountMinSketch(eps, delta)
        assert cms.width == w == math.ceil(math.e / eps), (eps, delta)
        assert cms.depth == d == math.ceil(math.log(1 / delta)), (eps, delta)


def test_bad_arguments():
    for eps, delta in [(0, 0.01), (1, 0.01), (-0.1, 0.01), (0.01, 0), (0.01, 1), (0.01, 2)]:
        with pytest.raises(ValueError):
            CountMinSketch(eps, delta)
    with pytest.raises(ValueError):
        CountMinSketch(0.01, 0.01).add("x", -1)


def test_add_with_counts_and_empty():
    cms = CountMinSketch(0.01, 0.01)
    assert cms.estimate("x") == 0 and cms.total == 0
    cms.add("x", 5)
    cms.add("x", 0)
    cms.add("y")
    assert cms.estimate("x") == 5 and cms.estimate("y") == 1 and cms.total == 6


def test_never_undercounts_and_meets_the_bound():
    eps, delta = 0.001, 0.01
    names, stream = skewed_stream(20_000, 150_000, seed=1)
    cms = CountMinSketch(eps, delta)
    for x in stream:
        cms.add(x)
    true = Counter(stream)
    n = len(stream)
    assert cms.total == n
    under = [x for x in names if cms.estimate(x) < true[x]]
    assert not under, f"{len(under)} items undercounted, e.g. {under[0]}: true {true[under[0]]}, estimate {cms.estimate(under[0])}"
    over = sum(cms.estimate(x) > true[x] + eps * n for x in names)
    assert over / len(names) <= delta, (
        f"{over:,} of {len(names):,} items ({over / len(names):.1%}) are over by more than epsilon * N = {eps * n:.0f}: "
        "is every row using its own independent hash, and is the answer the minimum over the rows?"
    )


def test_memory_does_not_grow_with_distinct_items():
    items = [f"user-{i}" for i in range(100_000)]
    tracemalloc.start()
    try:
        cms = CountMinSketch(0.001, 0.01)
        for x in items:
            cms.add(x)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak <= 1_000_000, f"peak {peak:,} bytes for {cms.width * cms.depth:,} counters: are the items themselves being stored?"
    assert all(cms.estimate(x) >= 1 for x in items[:500])


def test_merge_equals_one_sketch_of_both_streams():
    _, stream = skewed_stream(3_000, 40_000, seed=2)
    left, right = stream[:15_000], stream[15_000:]
    a, b, both = CountMinSketch(0.005, 0.01), CountMinSketch(0.005, 0.01), CountMinSketch(0.005, 0.01)
    for x in left:
        a.add(x)
        both.add(x)
    for x in right:
        b.add(x)
        both.add(x)
    probe = sorted(set(stream))[:2000] + ["never-seen"]
    a_before = [a.estimate(x) for x in probe]
    m = a.merge(b)
    assert m is not a and m is not b
    assert m.total == len(stream)
    assert [m.estimate(x) for x in probe] == [both.estimate(x) for x in probe]
    assert [a.estimate(x) for x in probe] == a_before, "merge() must not modify its inputs"


def test_merge_needs_matching_shapes():
    with pytest.raises(ValueError):
        CountMinSketch(0.01, 0.01).merge(CountMinSketch(0.001, 0.01))
    with pytest.raises(ValueError):
        CountMinSketch(0.01, 0.01).merge(CountMinSketch(0.01, 0.001))


SCRIPT = """
import sys
from count_min_sketch import CountMinSketch
cms = CountMinSketch(0.05, 0.01)  # tiny: 55 columns, so 2,000 items collide a lot
for i in range(2000):
    cms.add(f"item-{i}", i % 7 + 1)
sys.stdout.write(",".join(str(cms.estimate(f"item-{i}")) for i in range(0, 2000, 10)))
"""


def test_estimates_are_the_same_in_every_process():
    outs = []
    for seed in ("0", "999"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        proc = subprocess.run([sys.executable, "-c", SCRIPT], cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr
        outs.append(proc.stdout)
    assert outs[0] == outs[1], "estimates depend on PYTHONHASHSEED: use hashlib, not the built-in hash()"


def test_heavy_hitters_small():
    assert heavy_hitters(iter("abracadabra"), 1) == [("a", 5)]
    assert heavy_hitters(iter("abracadabra"), 3) == [("a", 5), ("b", 2), ("r", 2)]
    assert heavy_hitters(iter([]), 3) == []
    assert heavy_hitters(iter("aab"), 5) == [("a", 2), ("b", 1)]


def heavy_stream(seed, late=None):
    rng = random.Random(seed)
    heavy = {f"bot-{i}": 2_000 * (11 - i) for i in range(1, 11)}  # 20,000 down to 2,000
    light = [f"user-{i}-{rng.getrandbits(24):06x}" for i in range(50_000)]
    stream = [h for h, c in heavy.items() if h != late for _ in range(c)]
    stream += [u for u in light for _ in range(rng.randint(1, 2))]
    rng.shuffle(stream)
    if late:
        stream += [late] * heavy[late]  # every copy of this one arrives at the very end
    return heavy, stream


@pytest.mark.parametrize("late", [None, "bot-3"])
def test_heavy_hitters_one_pass_little_memory(late):
    heavy, stream = heavy_stream(3, late)
    n = len(stream)
    tracemalloc.start()
    try:
        got = heavy_hitters((x for x in stream), 10, epsilon=0.001)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    want = sorted(heavy, key=lambda h: -heavy[h])
    assert [x for x, _ in got] == want, f"got {[x for x, _ in got]}"
    for x, est in got:
        assert heavy[x] <= est <= heavy[x] + 0.001 * n, (x, est, heavy[x])
    assert peak <= 1_500_000, f"peak {peak:,} bytes for 50,000+ distinct items: is a count being kept for every one of them?"
