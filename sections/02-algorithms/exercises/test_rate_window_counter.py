import ast
import inspect
import math
import random
import signal
import time
import tracemalloc

import pytest

import rate_window_counter
from rate_window_counter import SlidingWindowCounter


@pytest.fixture(autouse=True)
def time_limit():
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is something looping over past requests?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class FakeClock:
    def __init__(self, start=0.0):
        self.t = float(start)
        self.reads = 0

    def __call__(self):
        self.reads += 1
        return self.t

    def advance(self, s):
        self.t += s


def brute_allowed(times, limit, window):
    """The rule from the docstring, worked out from a full list of allowed
    times (slow and memory-hungry on purpose). Small inputs only."""
    acc, out = [], []
    for t in times:
        w = math.floor(t / window)
        cur = sum(1 for a in acc if math.floor(a / window) == w)
        prev = sum(1 for a in acc if math.floor(a / window) == w - 1)
        elapsed = t - w * window
        ok = prev * (window - elapsed) / window + cur + 1 <= limit
        out.append(ok)
        if ok:
            acc.append(t)
    return out


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------
def test_prompt_example():
    c = FakeClock(10)
    r = SlidingWindowCounter(limit=100, window=60, clock=c)
    assert sum(r.allow("u") for _ in range(80)) == 80
    c.t = 75
    assert sum(r.allow("u") for _ in range(30)) == 30
    assert r.estimate("u") == pytest.approx(90.0)
    assert [r.allow("u") for _ in range(11)] == [True] * 10 + [False]
    assert r.estimate("u") == pytest.approx(100.0)


def test_boundary_burst_is_blocked():
    """Fixed window: 100 at t=59 and 100 more at t=60 all pass. Here: none of the second 100."""
    c = FakeClock(59)
    r = SlidingWindowCounter(100, 60, clock=c)
    assert sum(r.allow("u") for _ in range(100)) == 100
    c.t = 60
    assert r.estimate("u") == pytest.approx(100.0)
    assert sum(r.allow("u") for _ in range(100)) == 0
    c.t = 90                          # half of the old window still overlaps: 50 left
    assert r.estimate("u") == pytest.approx(50.0)
    assert sum(r.allow("u") for _ in range(100)) == 50


def test_window_rollover_and_skip():
    c = FakeClock(0)
    r = SlidingWindowCounter(10, 8, clock=c)
    for _ in range(6):
        r.allow("k")
    c.t = 10                          # window 1, elapsed 2: 6 * 6/8 + 0
    assert r.estimate("k") == pytest.approx(4.5)
    assert sum(r.allow("k") for _ in range(10)) == 5     # 4.5 + 5 + 1 > 10 stops the 6th
    c.t = 16                          # window 2: previous is now window 1's 5
    assert r.estimate("k") == pytest.approx(5.0)
    c.t = 40                          # window 5: skipped windows 3 and 4, so both counts reset
    assert r.estimate("k") == 0.0
    assert sum(r.allow("k") for _ in range(20)) == 10


def test_rejected_requests_are_not_counted():
    c = FakeClock(0)
    r = SlidingWindowCounter(10, 10, clock=c)
    passed = 0
    for _ in range(2000):             # 20 per second for 100 s, limit 1 per second
        passed += r.allow("loud")
        c.advance(0.05)
    assert 85 <= passed <= 100        # never more than 10 per 10 s on average


def test_estimate_changes_nothing():
    c = FakeClock(0)
    r = SlidingWindowCounter(3, 5, clock=c)
    assert r.estimate("ghost") == 0.0
    for _ in range(50):
        r.estimate("a")
    assert [r.allow("a") for _ in range(4)] == [True, True, True, False]


def test_bad_arguments():
    for limit, window in [(0, 1), (-3, 1), (1, 0), (4, -1)]:
        with pytest.raises(ValueError):
            SlidingWindowCounter(limit, window, clock=FakeClock())


def test_matches_brute_force_on_random_traffic():
    rng = random.Random(1403)
    for _ in range(60):
        limit, window = rng.randint(1, 6), rng.choice([2, 4, 8])
        times, t = [], 0.0
        for _ in range(rng.randint(1, 80)):
            t += rng.choice([0, 0, 0.25, 0.5, 1, 2, 3.75])
            times.append(t)
        c = FakeClock()
        r = SlidingWindowCounter(limit, window, clock=c)
        got = []
        for x in times:
            c.t = x
            got.append(r.allow("k"))
        assert got == brute_allowed(times, limit, window)


def test_keys_are_independent():
    c = FakeClock(0)
    r = SlidingWindowCounter(2, 10, clock=c)
    assert [r.allow("a"), r.allow("a"), r.allow("a")] == [True, True, False]
    assert [r.allow("b"), r.allow("b"), r.allow("b")] == [True, True, False]


# ---------------------------------------------------------------------------
# Memory and work
# ---------------------------------------------------------------------------
def test_one_busy_key_uses_constant_memory():
    """Huge limit, 300,000 allowed requests: a counter stays the same size; a log grows."""
    c = FakeClock(0)
    r = SlidingWindowCounter(10**9, 10**6, clock=c)
    for _ in range(1000):
        r.allow("k")
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for _ in range(300_000):
        assert r.allow("k")
        c.advance(0.001)
    after = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    assert after - before < 20_000, f"grew by {after - before:,} bytes: store counts, not timestamps"


def test_memory_per_key_is_small():
    """100,000 keys with 3 requests each. Three small numbers per key cost
    about 200 bytes with Python's overheads; a deque per key costs over 600."""
    c = FakeClock(0)
    r = SlidingWindowCounter(5, 60, clock=c)
    keys = [f"k{i}" for i in range(100_000)]
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for k in keys:
        r.allow(k)
        r.allow(k)
        r.allow(k)
    per_key = (tracemalloc.get_traced_memory()[0] - before) / len(keys)
    tracemalloc.stop()
    assert per_key < 400, f"{per_key:.0f} bytes per key: keep two counts and a window number"


def test_reads_clock_at_most_once_per_call():
    c = FakeClock(0)
    r = SlidingWindowCounter(3, 2, clock=c)
    for k in range(1, 41):
        before = c.reads
        (r.allow if k % 2 else r.estimate)("a")
        c.advance(0.3)
        assert c.reads - before <= 1, "read the clock once per call, then use that one value"


def test_default_clock_is_monotonic():
    default = inspect.signature(SlidingWindowCounter.__init__).parameters["clock"].default
    assert default is time.monotonic


def test_no_timers_threads_or_wall_clock():
    banned_modules = {"threading", "_thread", "sched", "asyncio", "multiprocessing", "concurrent", "datetime"}
    tree = ast.parse(inspect.getsource(rate_window_counter))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in banned_modules, f"don't import {a.name}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_modules, f"don't import from {node.module}"
            if node.module == "time":
                bad = {a.name for a in node.names} & {"time", "time_ns", "sleep"}
                assert not bad, f"don't import {bad} from time"
        elif isinstance(node, ast.Attribute):
            assert node.attr != "sleep", "no sleeping"
            if isinstance(node.value, ast.Name) and node.value.id == "time":
                assert node.attr not in ("time", "time_ns"), "use the injected clock, not the wall clock"
