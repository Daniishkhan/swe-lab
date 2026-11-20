import random
import signal

import pytest

from lfu_cache import LFUCache


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with O(1) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is eviction scanning every entry for the fewest uses?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class K:
    """A key that counts every __hash__ and __eq__ call (class-wide)."""

    __slots__ = ("v",)
    calls = 0

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        K.calls += 1
        return hash(self.v)

    def __eq__(self, other):
        K.calls += 1
        return isinstance(other, K) and self.v == other.v

    def __repr__(self):
        return f"K({self.v})"


class Model:
    """Slow, but simple enough to check by reading it: scan for (fewest uses, oldest last use)."""

    def __init__(self, capacity):
        self.cap, self.d, self.t = capacity, {}, 0  # key -> [value, uses, last_use]

    def get(self, k, default=None):
        if k not in self.d:
            return default
        self.t += 1
        e = self.d[k]
        e[1] += 1
        e[2] = self.t
        return e[0]

    def put(self, k, v):
        self.t += 1
        if k in self.d:
            e = self.d[k]
            e[0], e[1], e[2] = v, e[1] + 1, self.t
            return
        if len(self.d) == self.cap:
            victim = min(self.d, key=lambda x: (self.d[x][1], self.d[x][2]))
            del self.d[victim]
        self.d[k] = [v, 1, self.t]

    def frequency(self, k):
        return self.d[k][1] if k in self.d else 0


def test_example():
    c = LFUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert c.get("b") is None
    assert c.get("c") == 3
    c.put("d", 4)
    assert "a" not in c and "c" in c and "d" in c
    assert c.frequency("c") == 2 and c.frequency("d") == 1 and c.frequency("a") == 0
    assert len(c) == 2


def test_invalid_capacity():
    for bad in (0, -3):
        with pytest.raises(ValueError):
            LFUCache(bad)


def test_capacity_one():
    c = LFUCache(1)
    c.put("x", 1)
    c.get("x")
    c.get("x")
    c.put("y", 2)  # x has 3 uses, but it's the only entry: it must go
    assert "x" not in c and c.get("y") == 2 and len(c) == 1


def test_ties_go_to_the_least_recently_used():
    c = LFUCache(3)
    for k in "abc":
        c.put(k, k)
    c.get("a")
    c.get("b")
    c.get("c")  # all at 2 uses; a is the least recent of them
    c.put("d", "d")
    assert "a" not in c and all(k in c for k in "bcd")
    c.get("b")  # b: 3 uses. c: 2. d: 1
    c.put("e", "e")  # d has the fewest uses
    assert "d" not in c and all(k in c for k in "bce")


def test_tie_break_is_recency_not_insertion_order():
    c = LFUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("b")
    c.get("a")  # both at 2 uses; a was inserted first but used last
    c.put("c", 3)
    assert "b" not in c and "a" in c


def test_update_counts_as_a_use_and_never_evicts():
    c = LFUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # a: 2 uses, new value, nothing evicted
    assert len(c) == 2 and c.frequency("a") == 2 and c.get("a") == 10
    c.put("c", 3)  # b has 1 use: evicted
    assert "b" not in c and c.get("a") == 10 and c.get("c") == 3


def test_new_key_lowers_the_minimum_back_to_one():
    c = LFUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    for _ in range(3):
        c.get("a")
        c.get("b")  # a: 4, b: 4, nothing has 1 use any more
    c.put("c", 3)  # evicts a (tie at 4, a is less recent); c has 1 use
    c.put("d", 4)  # now c must go: it has the fewest uses, not b
    assert "c" not in c and "b" in c and "d" in c
    assert c.frequency("b") == 4 and c.frequency("d") == 1


def test_evicted_key_starts_over():
    c = LFUCache(1)
    c.put("a", 1)
    for _ in range(5):
        c.get("a")
    c.put("b", 2)
    c.put("a", 3)
    assert c.frequency("a") == 1 and c.get("a") == 3


def test_queries_do_not_count_as_uses():
    c = LFUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("b")
    for _ in range(5):
        assert "a" in c and c.frequency("a") == 1 and len(c) == 2
    assert c.get("zzz", -1) == -1
    c.put("c", 3)
    assert "a" not in c


def test_none_values():
    c = LFUCache(2)
    c.put("a", None)
    assert "a" in c and c.get("a", "missing") is None and c.frequency("a") == 2


def test_random_against_model():
    rng = random.Random(21)
    for _ in range(60):
        cap = rng.randint(1, 7)
        c, m = LFUCache(cap), Model(cap)
        for _ in range(300):
            k, r = rng.randint(0, 10), rng.random()
            if r < 0.45:
                assert c.get(k, -1) == m.get(k, -1)
            elif r < 0.9:
                v = rng.randint(0, 99)
                c.put(k, v)
                m.put(k, v)
            else:
                assert c.frequency(k) == m.frequency(k)
                assert (k in c) == (k in m.d)
            assert len(c) == len(m.d)
        for k in range(11):
            assert c.frequency(k) == m.frequency(k), k


def run_counted(cap, ops, seed):
    rng = random.Random(seed)
    c = LFUCache(cap)
    for i in range(cap):
        c.put(K(i), i)
    K.calls = 0
    for _ in range(ops):
        k = K(rng.randrange(3 * cap))  # a fresh, equal key object: lookups really compare
        r = rng.random()
        if r < 0.5:
            c.get(k)
        elif r < 0.9:
            c.put(k, 1)
        else:
            c.frequency(k)
    assert len(c) == cap
    return K.calls


def test_hash_and_eq_calls_are_constant_per_operation():
    ops = 20_000
    calls = run_counted(2_000, ops, seed=5)
    assert calls <= 10 * ops, (
        f"{calls:,} __hash__/__eq__ calls for {ops:,} operations ({calls / ops:.0f} each, budget 10): "
        "is something scanning the keys to find the one with the fewest uses?"
    )


def test_many_operations_quickly():
    rng = random.Random(13)
    cap = 50_000
    c = LFUCache(cap)
    hot = [rng.randrange(10 ** 9) for _ in range(cap // 2)]
    for i in range(300_000):
        if i % 2:
            k = rng.choice(hot)  # repeat customers pile up uses
        else:
            k = rng.randrange(10 ** 9)  # one-off keys: each new one evicts
        if i % 3 == 0:
            c.get(k)
        else:
            c.put(k, i)
    assert len(c) == cap
    assert sum(k in c for k in hot) > cap // 3, "the frequently used keys should mostly survive"
