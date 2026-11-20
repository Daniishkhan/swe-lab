import ast
import inspect
import itertools
import random
import signal
import tracemalloc
from collections import Counter

import pytest

import reservoir_sample as solution
from reservoir_sample import reservoir_sample, weighted_reservoir_sample


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes a couple of seconds at most (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 30 s cap: is something re-reading or sorting the whole stream?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def chi_square(observed, expected):
    return sum((observed.get(key, 0) - e) ** 2 / e for key, e in expected.items())


def once(items):
    """An iterator that can be read only once, like a real stream."""
    return (x for x in items)


# ---------------------------------------------------------------- uniform


def test_returns_k_distinct_items_from_the_stream():
    rng = random.Random(1)
    out = reservoir_sample(once(range(1000)), 10, rng)
    assert isinstance(out, list)
    assert len(out) == 10
    assert len(set(out)) == 10, "sampling is without replacement: no item twice"
    assert all(0 <= x < 1000 for x in out)


def test_short_stream_returns_everything():
    rng = random.Random(2)
    assert sorted(reservoir_sample(once("ab"), 5, rng)) == ["a", "b"]
    assert sorted(reservoir_sample(once(range(4)), 4, rng)) == [0, 1, 2, 3]
    assert reservoir_sample(once([]), 3, rng) == []
    assert reservoir_sample(once(range(10)), 0, rng) == []


def test_duplicates_in_the_stream_are_separate_items():
    rng = random.Random(3)
    out = reservoir_sample(once(["x"] * 50), 3, rng)
    assert out == ["x", "x", "x"]


def test_seeded_runs_repeat():
    a = reservoir_sample(once(range(500)), 7, random.Random(42))
    b = reservoir_sample(once(range(500)), 7, random.Random(42))
    assert sorted(a) == sorted(b), "use only the rng you were given"


def test_every_subset_equally_likely():
    # 6 items, k = 2: 15 possible pairs, each with chance 1/15.
    rng = random.Random(2026)
    trials = 30_000
    seen = Counter(frozenset(reservoir_sample(once(range(6)), 2, rng)) for _ in range(trials))
    expected = {frozenset(p): trials / 15 for p in itertools.combinations(range(6), 2)}
    assert set(seen) <= set(expected)
    stat = chi_square(seen, expected)
    # 14 degrees of freedom: a fair sampler scores about 14 and almost never
    # above 45. Keeping line i (counted from 1) with k/(i-1) instead of k/i
    # scores in the thousands.
    assert stat < 60, f"some pairs come up far too often or too rarely (chi-square {stat:.0f}): {dict(seen)}"


def test_every_item_equally_likely():
    # 20 items, k = 5: each item should be in the sample 1/4 of the time.
    rng = random.Random(7)
    trials = 20_000
    seen = Counter()
    for _ in range(trials):
        seen.update(reservoir_sample(once(range(20)), 5, rng))
    expected = {i: trials * 5 / 20 for i in range(20)}
    stat = chi_square(seen, expected)
    early, late = seen[0], seen[19]
    assert stat < 80, f"items are not equally likely (chi-square {stat:.0f}); first item {early}, last item {late}, want about {trials // 4} each"


def test_long_stream_has_no_recency_bias():
    # 500 items, k = 10, grouped into ten blocks of 50 positions.
    rng = random.Random(11)
    trials = 1000
    blocks = Counter()
    for _ in range(trials):
        blocks.update(x // 50 for x in reservoir_sample(once(range(500)), 10, rng))
    expected = {b: trials * 10 / 10 for b in range(10)}
    stat = chi_square(blocks, expected)
    assert stat < 50, f"early and late lines are not equally likely: hits per block of 50 lines {[blocks[b] for b in range(10)]}"


def test_memory_is_order_k():
    n = 200_000
    stream = (i * 1_000_003 for i in range(n))  # fresh int objects, not cached small ints
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        out = reservoir_sample(stream, 10, random.Random(5))
        assert tracemalloc.is_tracing(), "don't switch off the memory measurement"
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert len(out) == 10
    assert peak < 64 * 1024, f"peak extra memory {peak:,} bytes for k = 10: are you storing the stream?"


# ---------------------------------------------------------------- weighted


def exact_pair_probabilities(weights):
    """Brute force: chance of each unordered pair when you pick 2 by weight, one at a time."""
    total = sum(weights)
    probs = Counter()
    for a, b in itertools.permutations(range(len(weights)), 2):
        probs[frozenset((a, b))] += weights[a] / total * weights[b] / (total - weights[a])
    return probs


def test_weighted_short_and_empty():
    rng = random.Random(1)
    assert weighted_reservoir_sample(once([]), 2, rng) == []
    assert weighted_reservoir_sample(once([("a", 1.0)]), 0, rng) == []
    assert sorted(weighted_reservoir_sample(once([("a", 1.0), ("b", 5.0)]), 3, rng)) == ["a", "b"]
    out = weighted_reservoir_sample(once([(i, 1 + i % 3) for i in range(100)]), 6, rng)
    assert len(out) == 6 and len(set(out)) == 6 and all(0 <= x < 100 for x in out)


def test_weighted_k1_is_proportional_to_weight():
    rng = random.Random(3)
    weights = [1, 2, 3, 4]
    trials = 20_000
    seen = Counter(weighted_reservoir_sample(once(list(zip("abcd", weights))), 1, rng)[0] for _ in range(trials))
    expected = {c: trials * w / 10 for c, w in zip("abcd", weights)}
    stat = chi_square(seen, expected)
    # 3 degrees of freedom. The tag u * w instead of u ** (1 / w) scores in the hundreds.
    assert stat < 30, f"picks are not proportional to weight 1:2:3:4: {dict(seen)}"


def test_weighted_k2_matches_one_at_a_time_picking():
    rng = random.Random(9)
    weights = [1.0, 2.0, 3.0, 4.0, 10.0]
    trials = 20_000
    seen = Counter(frozenset(weighted_reservoir_sample(once(list(enumerate(weights))), 2, rng)) for _ in range(trials))
    expected = {pair: p * trials for pair, p in exact_pair_probabilities(weights).items()}
    stat = chi_square(seen, expected)
    assert stat < 50, f"pair frequencies don't match picking by weight without replacement (chi-square {stat:.0f})"


def test_weighted_equal_weights_is_uniform():
    rng = random.Random(4)
    trials = 15_000
    seen = Counter(frozenset(weighted_reservoir_sample(once([(i, 2.5) for i in range(5)]), 2, rng)) for _ in range(trials))
    expected = {frozenset(p): trials / 10 for p in itertools.combinations(range(5), 2)}
    assert chi_square(seen, expected) < 45


def test_weighted_memory_is_order_k():
    n = 100_000
    stream = ((i * 1_000_003, 1.0 + i % 7) for i in range(n))
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        out = weighted_reservoir_sample(stream, 10, random.Random(6))
        assert tracemalloc.is_tracing(), "don't switch off the memory measurement"
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert len(out) == 10
    assert peak < 64 * 1024, f"peak extra memory {peak:,} bytes for k = 10: are you storing the stream?"


# ---------------------------------------------------------------- fair play


# The tests measure time, memory and work. A solution has no reason to import
# the measuring tools or the tests themselves.
OFF_LIMITS = {"tracemalloc", "gc", "signal", "ctypes"}


def imported_modules(module):
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    return names


def test_does_not_import_the_measuring_tools():
    bad = sorted(n for n in imported_modules(solution) if n in OFF_LIMITS or n.startswith("test_"))
    assert not bad, f"the solution doesn't need these imports: {bad}"
