import ast
import inspect
import random
import signal
import time
import tracemalloc

import pytest

import rate_window_log
from rate_window_log import SlidingWindowLog


@pytest.fixture(autouse=True)
def time_limit():
    """Every test here takes about a second or less with an amortized O(1) log (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 8 s: is something scanning or copying the whole log on every request?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(8)
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
    """The definition, by brute force: accept t if fewer than `limit`
    accepted requests are in (t - window, t]. Small inputs only."""
    acc, out = [], []
    for t in times:
        ok = sum(1 for a in acc if t - a < window) < limit
        out.append(ok)
        if ok:
            acc.append(t)
    return out


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------
def test_prompt_example():
    c = FakeClock()
    w = SlidingWindowLog(limit=3, window=10, clock=c)
    out = []
    for t in (0, 4, 5, 9):
        c.t = t
        out.append(w.allow("ana"))
    assert out == [True, True, True, False]
    assert w.retry_after("ana") == pytest.approx(1.0)
    assert w.count("ana") == 3
    c.t = 10
    assert w.retry_after("ana") == 0.0
    assert w.allow("ana") is True
    assert w.count("ana") == 3
    assert w.allow("bob") is True
    assert w.count("bob") == 1


def test_expires_exactly_at_t_plus_window():
    c = FakeClock()
    w = SlidingWindowLog(1, 8, clock=c)
    assert w.allow("k")
    c.t = 7.999
    assert not w.allow("k")
    c.t = 8.0
    assert w.allow("k")


def test_no_boundary_burst():
    """The fixed-window trap: 5 at t=59, 5 at t=60. An exact log says no to the second 5."""
    c = FakeClock(59)
    w = SlidingWindowLog(5, 60, clock=c)
    assert sum(w.allow("u") for _ in range(5)) == 5
    c.t = 60
    assert sum(w.allow("u") for _ in range(5)) == 0
    c.t = 119
    assert sum(w.allow("u") for _ in range(5)) == 5


def test_rejected_requests_are_not_logged():
    """A client retrying at twice the limit still gets `limit` per window, every window."""
    c = FakeClock()
    w = SlidingWindowLog(10, 10, clock=c)
    passed = []
    for _ in range(2000):            # 20 per second for 100 s
        passed.append(w.allow("loud"))
        c.advance(0.05)
    per_window = [sum(passed[i:i + 200]) for i in range(0, 2000, 200)]
    assert per_window == [10] * 10


def test_count_drops_expired_requests():
    """count() answers for right now: requests that left the window don't count,
    even if no allow() has run since."""
    c = FakeClock()
    w = SlidingWindowLog(3, 10, clock=c)
    for t in (0, 2, 4):
        c.t = t
        w.allow("ana")
    c.t = 13
    assert w.count("ana") == 1        # 0 and 2 have left; 4 is still in
    c.t = 14
    assert w.count("ana") == 0


def test_count_and_peek_do_not_log_or_create():
    c = FakeClock()
    w = SlidingWindowLog(2, 5, clock=c)
    assert w.count("ghost") == 0
    assert w.retry_after("ghost") == 0.0
    assert w.forget_idle() == 0
    for _ in range(20):
        w.count("ana")
        w.retry_after("ana")
    assert w.allow("ana") and w.allow("ana") and not w.allow("ana")


def test_bad_arguments():
    for limit, window in [(0, 1), (-1, 1), (1, 0), (2, -5)]:
        with pytest.raises(ValueError):
            SlidingWindowLog(limit, window, clock=FakeClock())


def test_matches_brute_force_on_random_traffic():
    rng = random.Random(1402)
    for _ in range(60):
        limit, window = rng.randint(1, 5), rng.choice([1, 2.5, 10])
        times, t = [], 0.0
        for _ in range(rng.randint(1, 60)):
            t += rng.choice([0, 0, 0.25, 0.5, 1, 2.5, 4])
            times.append(t)
        c = FakeClock()
        w = SlidingWindowLog(limit, window, clock=c)
        got = []
        for x in times:
            c.t = x
            got.append(w.allow("k"))
        assert got == brute_allowed(times, limit, window)


def test_many_keys_are_independent():
    rng = random.Random(7)
    c = FakeClock()
    w = SlidingWindowLog(3, 4, clock=c)
    per_key = {k: [] for k in "abcde"}
    for _ in range(400):
        c.advance(rng.choice([0, 0.5, 1]))
        k = rng.choice("abcde")
        per_key[k].append((c.t, w.allow(k)))
    for k, rows in per_key.items():
        assert [ok for _, ok in rows] == brute_allowed([t for t, _ in rows], 3, 4)


# ---------------------------------------------------------------------------
# Work and memory
# ---------------------------------------------------------------------------
def test_big_limit_is_still_fast():
    """limit 400,000 and 800,000 requests. A deque does about 1 push and 1 pop
    per request (well under a second). Filtering the whole log each time is
    ~400,000 steps per request, and list.pop(0) shifts the whole list: both
    are far over the time limit."""
    c = FakeClock()
    w = SlidingWindowLog(400_000, 2000, clock=c)
    passed = 0
    for _ in range(800_000):
        passed += w.allow("big")
        c.advance(0.004)
    # 0-1600 s: 400,000 pass; from 2000 s on, each expiry lets one more in (300,000)
    assert 699_990 <= passed <= 700_010
    assert w.count("big") <= 400_000


def test_old_timestamps_are_thrown_away():
    """One key, limit 10, 200,000 requests over 2,000 s: at most 10 timestamps alive."""
    c = FakeClock()
    w = SlidingWindowLog(10, 1, clock=c)
    for _ in range(1000):
        w.allow("k")
        c.advance(0.01)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for _ in range(200_000):
        w.allow("k")
        c.advance(0.01)
    after = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    assert after - before < 20_000, f"grew by {after - before:,} bytes: old or rejected timestamps are being kept"


def test_forget_idle_frees_memory():
    c = FakeClock()
    w = SlidingWindowLog(5, 10, clock=c)
    keys = [f"user-{i}" for i in range(20_000)]
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    for k in keys:
        w.allow(k)
    full = tracemalloc.get_traced_memory()[0]
    c.advance(10)                     # every request has now left its window
    assert w.forget_idle() == 20_000
    left = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    grown = full - base
    assert grown > 0
    assert left - base < 0.5 * grown, (
        f"after forget_idle {left - base:,} of {grown:,} bytes are still held: delete the keys, not just their contents")
    assert w.forget_idle() == 0
    assert w.allow("user-1") is True


def test_forget_idle_keeps_active_keys():
    c = FakeClock()
    w = SlidingWindowLog(2, 10, clock=c)
    w.allow("old")
    c.t = 6
    w.allow("mid")
    w.allow("mid")
    c.t = 12                          # "old" (t=0) is out; "mid" (t=6) is still in
    assert w.forget_idle() == 1
    assert w.count("mid") == 2
    assert w.allow("mid") is False
    assert w.count("old") == 0


def test_reads_clock_at_most_once_per_call():
    c = FakeClock()
    w = SlidingWindowLog(3, 2, clock=c)
    calls = [lambda: w.allow("a"), lambda: w.count("a"), lambda: w.retry_after("a"), w.forget_idle]
    for k in range(1, 41):
        before = c.reads
        calls[k % 4]()
        c.advance(0.3)
        assert c.reads - before <= 1, "read the clock once per call, then use that one value"


def test_default_clock_is_monotonic():
    default = inspect.signature(SlidingWindowLog.__init__).parameters["clock"].default
    assert default is time.monotonic


def test_no_timers_threads_or_wall_clock():
    banned_modules = {"threading", "_thread", "sched", "asyncio", "multiprocessing", "concurrent", "datetime"}
    tree = ast.parse(inspect.getsource(rate_window_log))
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
