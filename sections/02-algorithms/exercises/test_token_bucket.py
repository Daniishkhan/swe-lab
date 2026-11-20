import ast
import inspect
import math
import random
import signal
import time
import tracemalloc

import pytest

import token_bucket
from token_bucket import TokenBucket


@pytest.fixture(autouse=True)
def time_limit():
    """Every test here takes well under a second with lazy refill (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is something looping per token, per tick, or per past request?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class FakeClock:
    """A clock the test moves by hand. Counts how often it is read."""

    def __init__(self, start=1000.0):
        self.t = float(start)
        self.reads = 0

    def __call__(self):
        self.reads += 1
        return self.t

    def advance(self, s):
        self.t += s


# ---------------------------------------------------------------------------
# The basics
# ---------------------------------------------------------------------------
def test_prompt_example():
    c = FakeClock()
    b = TokenBucket(capacity=5, rate=2, clock=c)
    assert [b.allow() for _ in range(5)] == [True] * 5
    assert b.allow() is False
    c.advance(0.75)
    assert b.allow() is True
    assert b.tokens() == pytest.approx(0.5)
    assert b.retry_after() == pytest.approx(0.25)


def test_starts_full_then_rejects():
    c = FakeClock()
    b = TokenBucket(5, 1, clock=c)
    assert b.tokens() == pytest.approx(5)
    assert all(b.allow() for _ in range(5))
    assert b.allow() is False


def test_refills_over_time():
    c = FakeClock()
    b = TokenBucket(5, 1, clock=c)
    for _ in range(5):
        b.allow()
    c.advance(1)
    assert b.allow() is True
    assert b.allow() is False


def test_fractional_refill():
    c = FakeClock()
    b = TokenBucket(1, 2, clock=c)
    assert b.allow()
    c.advance(0.25)
    assert b.tokens() == pytest.approx(0.5)
    assert b.allow() is False
    c.advance(0.25)
    assert b.allow() is True


def test_never_exceeds_capacity():
    c = FakeClock()
    b = TokenBucket(3, 10, clock=c)
    c.advance(1000)
    assert b.tokens() == pytest.approx(3)
    assert sum(b.allow() for _ in range(10)) == 3


def test_cost_and_rejection_spends_nothing():
    c = FakeClock()
    b = TokenBucket(5, 1, clock=c)
    assert b.allow(cost=4)
    assert b.allow(cost=2) is False
    assert b.tokens() == pytest.approx(1)
    assert b.allow(cost=1) is True
    assert b.allow(cost=10) is False
    assert b.tokens() == pytest.approx(0)


def test_fractional_costs():
    c = FakeClock()
    b = TokenBucket(2, 1, clock=c)
    assert b.allow(0.5) and b.allow(0.5) and b.allow(0.75)
    assert b.tokens() == pytest.approx(0.25)
    assert b.allow(0.5) is False


def test_bad_arguments():
    c = FakeClock()
    for cap, rate in [(0, 1), (-1, 1), (1, 0), (1, -2)]:
        with pytest.raises(ValueError):
            TokenBucket(cap, rate, clock=c)
    b = TokenBucket(1, 1, clock=c)
    for cost in (0, -1):
        with pytest.raises(ValueError):
            b.allow(cost)


def test_peeking_spends_nothing():
    c = FakeClock()
    b = TokenBucket(3, 1, clock=c)
    for _ in range(50):
        b.tokens()
        b.retry_after(2)
    assert b.tokens() == pytest.approx(3)
    assert sum(b.allow() for _ in range(5)) == 3


# ---------------------------------------------------------------------------
# The burst-plus-rate guarantee: over any T seconds, at most capacity + rate*T
# ---------------------------------------------------------------------------
def test_long_run_rate_and_burst():
    """Hammer it 100 times a second for 60 s: capacity 10, rate 2/s.
    Exactly 10 (the full jar) + 2 * 60 (the tap) can pass."""
    c = FakeClock(0)
    b = TokenBucket(10, 2, clock=c)
    passed = 0
    for _ in range(6000):
        passed += b.allow()
        c.advance(0.01)
    # the last 0.01 s of refill is in the jar, not spent
    assert passed in (130, 129)


def test_guarantee_on_random_traffic():
    """Brute-force check: in every window [s, s+T], passed <= capacity + rate*T."""
    rng = random.Random(14)
    for _ in range(30):
        cap, rate = rng.choice([1, 2, 5]), rng.choice([0.5, 1, 4])
        c = FakeClock(0)
        b = TokenBucket(cap, rate, clock=c)
        times = []
        for _ in range(300):
            c.advance(rng.choice([0, 0, 0.01, 0.1, 0.25, 1, 3]))
            if b.allow():
                times.append(c.t)
        for i in range(len(times)):
            for j in range(i, len(times)):
                assert j - i + 1 <= cap + rate * (times[j] - times[i]) + 1e-9


# ---------------------------------------------------------------------------
# retry_after
# ---------------------------------------------------------------------------
def test_retry_after_is_exact():
    c = FakeClock()
    b = TokenBucket(4, 2, clock=c)
    assert b.retry_after(3) == 0.0
    assert b.allow(3)                 # 1 left
    assert b.retry_after(1) == 0.0
    assert b.retry_after(3) == pytest.approx(1.0)   # needs 2 more at 2/s
    wait = b.retry_after(4)
    assert wait == pytest.approx(1.5)
    c.advance(wait - 0.01)
    assert b.allow(4) is False
    c.advance(0.01 + 1e-9)
    assert b.allow(4) is True


def test_retry_after_counts_time_that_passed():
    """retry_after must refill first, like allow does: time passes between calls."""
    c = FakeClock()
    b = TokenBucket(4, 2, clock=c)
    assert b.allow(4)                 # empty
    assert b.retry_after(4) == pytest.approx(2.0)
    c.advance(0.5)                    # 1 token back
    assert b.retry_after(4) == pytest.approx(1.5)
    assert b.retry_after(1) == 0.0
    c.advance(10)                     # full again
    assert b.retry_after(4) == 0.0


def test_retry_after_impossible():
    c = FakeClock()
    b = TokenBucket(4, 2, clock=c)
    assert b.retry_after(5) == math.inf
    assert b.allow(5) is False


def test_retry_after_then_wait_always_works():
    rng = random.Random(214)
    c = FakeClock()
    b = TokenBucket(7, 3, clock=c)
    for _ in range(500):
        cost = rng.choice([1, 2, 3.5, 7])
        if not b.allow(cost):
            w = b.retry_after(cost)
            assert 0 < w < math.inf
            c.advance(w + 1e-9)
            assert b.allow(cost), "waiting retry_after() seconds must be enough"
        c.advance(rng.choice([0, 0.1, 0.5]))


# ---------------------------------------------------------------------------
# Lazy refill, clocks, and memory
# ---------------------------------------------------------------------------
def test_huge_idle_gap_is_instant():
    """A billion seconds idle at a million tokens a second: a refill loop never ends."""
    c = FakeClock()
    b = TokenBucket(5, 1_000_000, clock=c)
    for _ in range(5):
        b.allow()
    c.advance(1e9)
    assert b.tokens() == pytest.approx(5, rel=0.01)   # floats near 1e9 are coarse
    assert sum(b.allow() for _ in range(9)) == 5


def test_huge_capacity_refills_instantly():
    """A billion-token jar, emptied, then left for two billion seconds at 1 token/s.
    A loop that adds a token (or a second) at a time, even one that stops when
    the jar is full, runs a billion times."""
    c = FakeClock()
    b = TokenBucket(10**9, 1, clock=c)
    assert b.allow(10**9)
    assert b.tokens() == pytest.approx(0, abs=1e-6)
    c.advance(2e9)
    assert b.tokens() == pytest.approx(10**9)
    assert b.allow(10**9) and not b.allow(1)


def test_clock_going_backwards_takes_nothing_and_adds_nothing():
    c = FakeClock()
    b = TokenBucket(10, 1, clock=c)
    for _ in range(6):
        b.allow()                     # 4 left
    c.advance(-30)                    # clock jumps back 30 s
    assert b.tokens() == pytest.approx(4), "a backwards jump must not take tokens away"
    assert sum(b.allow() for _ in range(10)) == 4
    c.advance(2)                      # 2 s pass after the jump
    assert b.tokens() == pytest.approx(2), "measure from the new reading after a jump"


def test_reads_clock_at_most_once_per_call():
    c = FakeClock()
    b = TokenBucket(3, 1, clock=c)
    for k in range(1, 31):
        before = c.reads
        [b.allow, b.tokens, b.retry_after][k % 3]()
        c.advance(0.2)
        assert c.reads - before <= 1, "read the clock once per call, then use that one value"


def test_default_clock_is_monotonic():
    default = inspect.signature(TokenBucket.__init__).parameters["clock"].default
    assert default is time.monotonic
    b = TokenBucket(2, 1)             # real clock: must work too
    assert b.allow() and b.allow() and not b.allow()


def test_memory_does_not_grow_with_requests():
    c = FakeClock()
    b = TokenBucket(1000, 500, clock=c)
    for _ in range(1000):
        b.allow()
        c.advance(0.001)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for _ in range(100_000):
        b.allow()
        c.advance(0.001)
    after = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    assert after - before < 20_000, f"grew by {after - before:,} bytes over 100,000 requests: keep O(1) state"


def test_no_timers_threads_or_wall_clock():
    """Lazy refill needs none of these. Checked on the code, not the comments."""
    banned_modules = {"threading", "_thread", "sched", "asyncio", "multiprocessing", "concurrent", "datetime"}
    tree = ast.parse(inspect.getsource(token_bucket))
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
            assert node.attr != "sleep", "no sleeping: compute the refill from elapsed time"
            if isinstance(node.value, ast.Name) and node.value.id == "time":
                assert node.attr not in ("time", "time_ns"), "use the injected clock, not the wall clock"
