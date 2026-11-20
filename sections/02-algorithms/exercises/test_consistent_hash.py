import hashlib
import os
import random
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from consistent_hash import ConsistentHashRing, stable_hash

HERE = Path(__file__).resolve().parent
KEYS = [f"user:{i}" for i in range(20000)]


@pytest.fixture(autouse=True)
def time_limit(request):
    """Every test finishes in about a second with bisect (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is a lookup scanning the points one by one instead of binary searching them?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def H(text):
    """The tests' own 64-bit hash, so ring tests don't depend on your stable_hash."""
    return int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "big")


class CountingHash:
    """Wraps a hash function and counts calls. With a budget, raises the moment it's exceeded."""

    def __init__(self, fn=H, budget=None):
        self.fn, self.calls, self.budget = fn, 0, budget

    def __call__(self, text):
        self.calls += 1
        if self.budget is not None and self.calls > self.budget:
            raise AssertionError(f"hash_fn called more than {self.budget} times here")
        return self.fn(text)


def ring_with(names, vnodes=100, hash_fn=H):
    r = ConsistentHashRing(vnodes=vnodes, hash_fn=hash_fn)
    for n in names:
        r.add_node(n)
    return r


def brute_points(names, vnodes, hash_fn):
    return sorted((hash_fn(f"{n}#{i}"), n) for n in names for i in range(vnodes))


def brute_walk(points, hash_fn, key):
    """Every node in the order a clockwise walk from the key meets it."""
    h = hash_fn(key)
    start = next((j for j, (p, _) in enumerate(points) if p >= h), 0)
    order = []
    for j in range(len(points)):
        n = points[(start + j) % len(points)][1]
        if n not in order:
            order.append(n)
    return order


# A toy clock with positions 0..99, so owners can be checked by eye.
CLOCK = {"A#0": 10, "B#0": 50, "C#0": 80,
         "A#1": 60, "B#1": 40, "C#1": 95}


def clock(label):
    return int(label[1:]) if label.startswith("k") else CLOCK[label]


# ---------------------------------------------------------------- the ring

def test_clockwise_owner_on_a_toy_clock():
    r = ring_with(["A", "B", "C"], vnodes=1, hash_fn=clock)   # A at 10, B at 50, C at 80
    assert r.get_node("k30") == "B"
    assert r.get_node("k79") == "C"
    assert r.get_node("k5") == "A"


def test_a_point_exactly_at_the_key_owns_it():
    r = ring_with(["A", "B", "C"], vnodes=1, hash_fn=clock)
    assert r.get_node("k10") == "A"
    assert r.get_node("k50") == "B"
    assert r.get_node("k80") == "C"


def test_wraps_around_past_the_last_point():
    r = ring_with(["A", "B", "C"], vnodes=1, hash_fn=clock)
    assert r.get_node("k81") == "A"
    assert r.get_node("k99") == "A"


def test_virtual_points_on_a_toy_clock():
    # A at 10 and 60, B at 40 and 50, C at 80 and 95
    r = ring_with(["A", "B", "C"], vnodes=2, hash_fn=clock)
    assert r.get_node("k45") == "B"     # next point is B#0 at 50
    assert r.get_node("k55") == "A"     # A#1 at 60
    assert r.get_node("k90") == "C"     # C#1 at 95
    assert r.get_node("k96") == "A"     # wraps to A#0 at 10


def test_empty_ring_raises():
    r = ConsistentHashRing(vnodes=10, hash_fn=H)
    with pytest.raises(LookupError):
        r.get_node("k")
    with pytest.raises(LookupError):
        r.get_nodes("k", 2)
    r.add_node("a")
    r.remove_node("a")
    with pytest.raises(LookupError):
        r.get_node("k")


def test_one_node_owns_everything():
    r = ring_with(["only"], vnodes=5)
    assert {r.get_node(k) for k in KEYS[:500]} == {"only"}


def test_add_twice_and_remove_missing_raise():
    r = ring_with(["a", "b"], vnodes=10)
    with pytest.raises(ValueError):
        r.add_node("a")
    with pytest.raises(KeyError):
        r.remove_node("zzz")


def test_matches_brute_force_on_random_rings():
    rng = random.Random(15)
    for trial in range(6):
        names = [f"n{rng.randrange(10**6)}" for _ in range(rng.randint(1, 7))]
        names = list(dict.fromkeys(names))
        vnodes = rng.choice([1, 3, 20, 50])
        r = ring_with(names, vnodes=vnodes)
        points = brute_points(names, vnodes, H)
        for k in rng.sample(KEYS, 300):
            assert r.get_node(k) == brute_walk(points, H, k)[0], (trial, k)


def test_insertion_order_does_not_matter():
    a = ring_with(["a", "b", "c", "d"], vnodes=40)
    b = ring_with(["d", "b", "a", "c"], vnodes=40)
    assert all(a.get_node(k) == b.get_node(k) for k in KEYS[:3000])


# ------------------------------------------------- adding and removing nodes

def test_adding_a_node_moves_about_one_in_n_plus_one():
    names = [f"cache-{i}" for i in range(10)]
    r = ring_with(names, vnodes=100)
    before = {k: r.get_node(k) for k in KEYS}
    r.add_node("cache-10")
    moved = [k for k in KEYS if r.get_node(k) != before[k]]
    frac = len(moved) / len(KEYS)
    assert 0.05 < frac < 0.16, f"{frac:.1%} of keys moved; expected about 1/11 = 9.1% (hash % N would move 91%)"
    assert all(r.get_node(k) == "cache-10" for k in moved), "a key moved between two old nodes"


def test_removing_a_node_moves_only_its_keys_and_spreads_them():
    names = [f"cache-{i}" for i in range(10)]
    r = ring_with(names, vnodes=100)
    before = {k: r.get_node(k) for k in KEYS}
    r.remove_node("cache-3")
    receivers = set()
    for k in KEYS:
        now = r.get_node(k)
        if before[k] == "cache-3":
            assert now != "cache-3"
            receivers.add(now)
        else:
            assert now == before[k], "a key that wasn't on the removed node moved"
    assert len(receivers) >= 7, "with 100 virtual points, the removed node's keys should spread over most nodes"


def test_add_then_remove_restores_every_owner():
    r = ring_with([f"n{i}" for i in range(6)], vnodes=30)
    before = [r.get_node(k) for k in KEYS[:5000]]
    r.add_node("tmp")
    r.remove_node("tmp")
    assert [r.get_node(k) for k in KEYS[:5000]] == before


def test_virtual_nodes_balance_the_load():
    r = ring_with([f"cache-{i}" for i in range(10)], vnodes=200)
    counts = {}
    for k in KEYS:
        n = r.get_node(k)
        counts[n] = counts.get(n, 0) + 1
    mean = len(KEYS) / 10
    assert len(counts) == 10
    assert max(counts.values()) < 1.35 * mean, f"busiest node has {max(counts.values()) / mean:.2f}x the average"
    assert min(counts.values()) > 0.65 * mean, f"quietest node has {min(counts.values()) / mean:.2f}x the average"


# ------------------------------------------------------------------ replicas

def test_replicas_on_a_toy_clock():
    r = ring_with(["A", "B", "C"], vnodes=2, hash_fn=clock)   # 10 A, 40 B, 50 B, 60 A, 80 C, 95 C
    assert r.get_nodes("k35", 1) == ["B"]
    assert r.get_nodes("k35", 2) == ["B", "A"], "B#0 at 50 is the same node as B#1 at 40: skip it"
    assert r.get_nodes("k35", 3) == ["B", "A", "C"]
    assert r.get_nodes("k90", 3) == ["C", "A", "B"], "wrap around after 95"
    assert r.get_nodes("k90", 10) == ["C", "A", "B"], "fewer nodes than k: return them all"


def test_replicas_start_at_a_point_exactly_at_the_key():
    r = ring_with(["A", "B", "C"], vnodes=2, hash_fn=clock)   # 10 A, 40 B, 50 B, 60 A, 80 C, 95 C
    assert r.get_nodes("k60", 3) == ["A", "C", "B"], "A#1 sits exactly at 60, so A is the first replica"
    assert r.get_nodes("k95", 3) == ["C", "A", "B"], "C#1 sits exactly at 95; then wrap to A at 10"
    assert r.get_nodes("k10", 1) == [r.get_node("k10")]


def test_replicas_walk_past_a_long_run_of_one_node():
    # Every point of A sits in one block (0..299), then B's (1000..1299), then
    # C's. From key 5 the walk must pass 295 of A's points before it meets B,
    # so a walk that gives up after a fixed number of steps is wrong.
    blocks = {"A": 0, "B": 1000, "C": 2000}

    def h(label):
        if label.startswith("k"):
            return int(label[1:])
        name, i = label.split("#")
        return blocks[name] + int(i)

    r = ring_with(["A", "B", "C"], vnodes=300, hash_fn=h)
    assert r.get_nodes("k5", 2) == ["A", "B"]
    assert r.get_nodes("k5", 3) == ["A", "B", "C"]
    assert r.get_nodes("k1500", 3) == ["C", "A", "B"]


def test_replicas_match_brute_force():
    rng = random.Random(7)
    names = [f"node-{i}" for i in range(8)]
    r = ring_with(names, vnodes=25)
    points = brute_points(names, 25, H)
    for k in rng.sample(KEYS, 300):
        order = brute_walk(points, H, k)
        for want in (1, 2, 3, 5):
            got = r.get_nodes(k, want)
            assert got == order[:want], (k, want)
        assert r.get_nodes(k, 1)[0] == r.get_node(k)


# ------------------------------------------------------------- measuring work

def test_hash_calls_per_operation():
    counter = CountingHash()
    r = ConsistentHashRing(vnodes=64, hash_fn=counter)
    for i in range(12):
        counter.calls, counter.budget = 0, 64
        r.add_node(f"node-{i}")
        assert counter.calls == 64, "add_node hashes each of its own points exactly once"
    for k in KEYS[:2000]:
        counter.calls, counter.budget = 0, 1
        r.get_node(k)
        counter.calls, counter.budget = 0, 1
        r.get_nodes(k, 3)
    counter.calls, counter.budget = 0, 64
    r.remove_node("node-5")


def test_big_ring_lookups_are_logarithmic():
    # 200 nodes x 500 points = 100,000 points. bisect needs about 17 steps per
    # lookup; a scan needs about 50,000. 50,000 lookups: ~1 s vs hours.
    r = ring_with([f"node-{i}" for i in range(200)], vnodes=500)
    seen = set()
    for k in KEYS + [f"session:{i}" for i in range(30000)]:
        seen.add(r.get_node(k))
    assert len(seen) == 200


def test_big_ring_replicas_stop_early():
    # Walking the whole ring for every get_nodes call is 100,000 steps each.
    # So is copying it: points[i:] + points[:i] costs about 0.5 ms a call, and
    # 150,000 calls of that is over a minute. Stopping after k nodes: under 1 s.
    r = ring_with([f"node-{i}" for i in range(200)], vnodes=500)
    for i in range(150000):
        got = r.get_nodes(f"user:{i}", 3)
        assert len(set(got)) == 3


# --------------------------------------------------------- the hash function

def test_stable_hash_range_and_spread():
    values = [stable_hash(f"key-{i}") for i in range(16000)]
    assert all(isinstance(v, int) and 0 <= v < 2**64 for v in values)
    assert len(set(values)) == len(values)
    assert max(values) >= 2**63, "use all 64 bits"
    low, high = [0] * 16, [0] * 16
    for v in values:
        low[v % 16] += 1
        high[v >> 60] += 1
    for counts in (low, high):
        assert max(counts) < 1150 and min(counts) > 850, f"uneven spread over 16 buckets: {counts}"


def test_stable_hash_is_the_default():
    r = ConsistentHashRing(vnodes=3)
    r.add_node("x")
    r.add_node("y")
    points = brute_points(["x", "y"], 3, stable_hash)
    for k in KEYS[:500]:
        assert r.get_node(k) == brute_walk(points, stable_hash, k)[0]


SNIPPET = """
import sys
sys.path.insert(0, sys.argv[1])
from consistent_hash import ConsistentHashRing, stable_hash
r = ConsistentHashRing(vnodes=20)
for i in range(5):
    r.add_node(f"node-{i}")
print([stable_hash(f"key-{i}") for i in range(30)])
print([r.get_node(f"user:{i}") for i in range(300)])
"""


def run_with_seed(seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run([sys.executable, "-c", SNIPPET, str(HERE)], env=env, cwd=HERE,
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_same_answers_in_every_process():
    first, second = run_with_seed(1), run_with_seed(2)
    assert first == second, "two processes with different PYTHONHASHSEED disagree: is something using hash() on a str?"
    here = [stable_hash(f"key-{i}") for i in range(30)]
    assert first.splitlines()[0] == str(here)
