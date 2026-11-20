import ast
import inspect
import random
import signal
import time
import tracemalloc

import pytest

import leaky_bucket
from leaky_bucket import LeakyBucket

EPS = 1e-9


@pytest.fixture(autouse=True)
def time_limit():
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 8 s: is something walking the whole queue on every call?")

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


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------
def test_prompt_example():
    c = FakeClock()
    b = LeakyBucket(rate=2, capacity=3, clock=c)
    assert [b.offer(x) for x in "abcde"] == [0.0, 0.5, 1.0, 1.5, None]
    assert b.poll() == ["a"]
    assert b.waiting() == 3
    c.t = 1.2
    assert b.poll() == ["b", "c"]
    assert b.waiting() == 1
    assert b.offer("f") == pytest.approx(0.8)
    assert b.poll() == []
    c.t = 2.0
    assert b.poll() == ["d", "f"]
    assert b.waiting() == 0


def test_burst_is_smoothed():
    """10 at once, rate 4/s, room for 4 to wait: 5 get through, 0.25 s apart."""
    c = FakeClock(100)
    b = LeakyBucket(4, 4, clock=c)
    delays = [b.offer(i) for i in range(10)]
    assert delays == [0.0, 0.25, 0.5, 0.75, 1.0, None, None, None, None, None]
    seen = []
    for _ in range(9):
        seen.append(b.poll())
        c.advance(0.125)
    assert seen == [[0], [], [1], [], [2], [], [3], [], [4]]


def test_idle_bucket_lets_the_next_one_straight_through():
    c = FakeClock()
    b = LeakyBucket(1, 2, clock=c)
    assert b.offer("x") == 0.0
    assert b.offer("y") == 1.0
    c.t = 10                          # long idle: the hole is free again
    assert b.offer("z") == 0.0
    assert b.poll() == ["x", "y", "z"]


def test_capacity_zero_means_no_waiting():
    c = FakeClock()
    b = LeakyBucket(2, 0, clock=c)
    assert b.offer(1) == 0.0
    assert b.offer(2) is None         # it would have to wait 0.5 s
    c.t = 0.5
    assert b.offer(3) == 0.0
    assert b.poll() == [1, 3]


def test_bad_arguments():
    for rate, cap in [(0, 1), (-1, 1), (1, -1)]:
        with pytest.raises(ValueError):
            LeakyBucket(rate, cap, clock=FakeClock())


def test_rules_hold_on_random_traffic():
    """Check every rule from the docstring on seeded random traffic."""
    rng = random.Random(1404)
    for _ in range(40):
        rate, cap = rng.choice([1, 2, 4, 8]), rng.randint(0, 6)
        gap = 1 / rate
        c = FakeClock(rng.choice([0, 37.5]))
        b = LeakyBucket(rate, cap, clock=c)
        last_leak = None
        leak_of, accepted, polled = {}, [], []
        for i in range(400):
            c.advance(rng.choice([0, 0, 0, 0.0625, 0.125, 0.5, 2]))
            if rng.random() < 0.2:
                got = b.poll()
                polled.extend(got)
                assert all(leak_of[x] <= c.t + EPS for x in got), "poll returned an item before its leak time"
                due = [x for x in accepted if leak_of[x] <= c.t + EPS]
                assert polled == due, "poll must return every due item, in order, once"
            before = b.waiting()
            assert before == sum(1 for x in accepted if leak_of[x] > c.t + EPS)
            assert before <= cap
            hole_free = last_leak is None or last_leak + gap <= c.t + EPS
            d = b.offer(i)
            if d is None:
                assert before >= cap and not hole_free, "rejected although there was room"
                continue
            assert d >= 0
            assert before < cap or d == 0, "accepted into a full bucket"
            leak = c.t + d
            if hole_free:
                assert d == pytest.approx(0, abs=EPS), "the hole was free: it should leak at once"
            else:
                assert leak == pytest.approx(last_leak + gap), "must leak exactly 1/rate after the previous one"
            last_leak = leak
            leak_of[i] = leak
            accepted.append(i)


# ---------------------------------------------------------------------------
# Work and memory
# ---------------------------------------------------------------------------
def test_huge_queue_is_still_fast():
    """capacity 200,000, rate 1,000/s, 400,000 offers at 2,000/s, waiting() every
    time, poll() only every 25 s. Counting by walking the queue is ~10^10 steps,
    and so is skipping the leaked-but-not-polled items at its front on every call
    (up to 25,000 of them pile up between polls)."""
    c = FakeClock()
    b = LeakyBucket(1000, 200_000, clock=c)
    accepted = out = 0
    for i in range(400_000):
        accepted += b.offer(i) is not None
        assert b.waiting() <= 200_000
        if i % 50_000 == 0:
            out += len(b.poll())
        c.advance(0.0005)
    assert 199_000 <= b.waiting() <= 200_000
    # half the offers fit through the hole over 200 s, plus the queue's worth
    assert 395_000 <= accepted <= 400_000


def test_memory_stays_bounded_when_polled():
    """Twice the rate for a long time, polling as we go: memory must not grow."""
    c = FakeClock()
    b = LeakyBucket(100, 50, clock=c)
    for i in range(2000):
        b.offer(i)
        b.poll()
        c.advance(0.005)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for i in range(200_000):
        b.offer(i)
        b.poll()
        c.advance(0.005)
    after = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    assert after - before < 30_000, f"grew by {after - before:,} bytes: drop rejected and polled items"


def test_reads_clock_at_most_once_per_call():
    c = FakeClock()
    b = LeakyBucket(2, 3, clock=c)
    calls = [lambda: b.offer("x"), b.poll, b.waiting]
    for k in range(1, 46):
        before = c.reads
        calls[k % 3]()
        c.advance(0.2)
        assert c.reads - before <= 1, "read the clock once per call, then use that one value"


def test_default_clock_is_monotonic():
    default = inspect.signature(LeakyBucket.__init__).parameters["clock"].default
    assert default is time.monotonic


def test_no_timers_threads_or_wall_clock():
    banned_modules = {"threading", "_thread", "sched", "asyncio", "multiprocessing", "concurrent", "datetime", "queue"}
    tree = ast.parse(inspect.getsource(leaky_bucket))
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
            assert node.attr != "sleep", "no sleeping: work out leak times from the clock"
            if isinstance(node.value, ast.Name) and node.value.id == "time":
                assert node.attr not in ("time", "time_ns"), "use the injected clock, not the wall clock"
