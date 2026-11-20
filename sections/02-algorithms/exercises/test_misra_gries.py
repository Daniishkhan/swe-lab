import ast
import inspect
import random
import signal
import tracemalloc
from collections import Counter

import pytest

import misra_gries as solution
from misra_gries import MisraGries, heavy_hitters


@pytest.fixture(autouse=True)
def time_limit(request):
    """A 10 s cap per test (Unix only). Done right, each takes well under a second."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 10 s cap: does every add() walk through all k counters?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def check_bounds(mg, truth, k):
    n = sum(truth.values())
    assert mg.n == n, f"n is {mg.n}, but {n} items were added"
    slack = n / (k + 1)
    for x, c in truth.items():
        e = mg.estimate(x)
        assert e <= c, f"estimate({x!r}) = {e} is above its true count {c}: Misra-Gries never overestimates"
        assert c <= e + slack, f"estimate({x!r}) = {e} but the true count is {c}: more than n/(k+1) = {slack:.1f} below"


def skewed(rng, n, distinct):
    """A few heavy items plus a long tail, like real traffic."""
    heavy = [f"h{i}" for i in range(5)]
    out = []
    for _ in range(n):
        r = rng.random()
        out.append(heavy[int(r * 20)] if r < 0.25 else rng.randrange(distinct))
    return out


def test_example():
    mg = MisraGries(2)
    for x in "aabacad":
        mg.add(x)
    assert mg.counters() == {"a": 3, "d": 1}
    assert mg.estimate("a") == 3 and mg.estimate("b") == 0 and mg.estimate("zzz") == 0
    assert mg.n == 7


def test_empty_and_counters_is_a_copy():
    mg = MisraGries(3)
    assert mg.n == 0 and mg.counters() == {} and mg.estimate("x") == 0
    mg.add("x")
    c = mg.counters()
    c["x"] = 99
    assert mg.estimate("x") == 1, "counters() must return a copy"


def test_k1_is_majority_vote():
    mg = MisraGries(1)
    for x in "abacaaba":  # a is 5 of 8: a majority
        mg.add(x)
    assert set(mg.counters()) == {"a"}


def test_bounds_after_every_add():
    rng = random.Random(1)
    for trial in range(200):
        k = rng.randint(1, 6)
        mg = MisraGries(k)
        truth = Counter()
        for _ in range(rng.randint(0, 80)):
            x = rng.choice("aaabbcdefgh")
            mg.add(x)
            truth[x] += 1
            assert len(mg.counters()) <= k, f"more than k = {k} counters"
            check_bounds(mg, truth, k)


def test_bounds_on_a_big_skewed_stream():
    rng = random.Random(2)
    k = 50
    stream = skewed(rng, 100_000, 50_000)
    mg = MisraGries(k)
    for x in stream:
        mg.add(x)
    assert len(mg.counters()) <= k
    truth = Counter(stream)
    check_bounds(mg, truth, k)
    for h in ("h0", "h1", "h2", "h3", "h4"):  # each is about 5% of the stream
        assert mg.estimate(h) > 0


def test_adversarial_order():
    # Heavy item first, then a flood of distinct items: it must survive.
    k = 9
    mg = MisraGries(k)
    stream = ["H"] * 200 + list(range(1500))
    for x in stream:
        mg.add(x)
    check_bounds(mg, Counter(stream), k)
    assert mg.estimate("H") > 0


def test_memory_is_order_k():
    n, distinct = 300_000, 100_000
    stream = ((i * 7919) % distinct * 1_000_003 for i in range(n))  # fresh int objects
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        mg = MisraGries(20)
        for x in stream:
            mg.add(x)
        assert tracemalloc.is_tracing(), "don't switch off the memory measurement"
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert mg.n == n and len(mg.counters()) <= 20
    assert peak < 64 * 1024, f"peak extra memory {peak:,} bytes for k = 20: are you counting every distinct item?"


def test_large_k_is_fast():
    # 10,000 items that stay heavy (20 copies each), then 220,000 new items. Done right: one O(1) step per
    # add, plus 20 walk-outs of 20,000 steps each. Looking at all k counters on every add (min of the
    # values, `0 in values`, a scan for a zero slot) is 230,000 x 10,000 or more: billions of steps.
    k = 20_000
    mg = MisraGries(k)
    for _ in range(20):
        for s in range(10_000):
            mg.add(s)
    for i in range(10_000, 230_000):
        mg.add(i)
    assert mg.n == 420_000 and len(mg.counters()) <= k


# ---------------------------------------------------------------- heavy_hitters


def brute(stream, k):
    n = len(stream)
    return {x: c for x, c in Counter(stream).items() if c > n / (k + 1)}


class Source:
    def __init__(self, items):
        self.items, self.calls = items, 0

    def __call__(self):
        self.calls += 1
        return (x for x in self.items)


def test_heavy_hitters_small():
    src = Source(list("aabacad"))
    assert heavy_hitters(src, 2) == {"a": 4}
    assert src.calls <= 2, "at most two passes"
    assert heavy_hitters(Source([]), 3) == {}
    assert heavy_hitters(Source(["x"]), 1) == {"x": 1}


def test_heavy_hitters_random_against_brute_force():
    rng = random.Random(3)
    for _ in range(300):
        k = rng.randint(1, 5)
        stream = [rng.choice("aaaabbbccdefg") for _ in range(rng.randint(0, 60))]
        src = Source(stream)
        assert heavy_hitters(src, k) == brute(stream, k), f"k = {k}, stream {''.join(stream)}"
        assert src.calls <= 2


def test_heavy_hitters_exact_threshold():
    # n = 12, k = 3: the threshold is n / (k + 1) = 3, and "greater than" is strict.
    stream = list("aaabbbbcdefg")
    assert heavy_hitters(Source(stream), 3) == {"b": 4}


def test_heavy_hitters_big_and_small_memory():
    rng = random.Random(4)
    stream = skewed(rng, 100_000, 50_000)
    want = brute(stream, 24)  # threshold n / 25 = 4,000; each heavy item is about 5,000
    assert set(want) == {"h0", "h1", "h2", "h3", "h4"}

    def make():
        return (x for x in stream)

    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        got = heavy_hitters(make, 24)
        assert tracemalloc.is_tracing(), "don't switch off the memory measurement"
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert got == want
    assert peak < 64 * 1024, f"peak extra memory {peak:,} bytes for k = 24: count only the candidates in pass 2"


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
