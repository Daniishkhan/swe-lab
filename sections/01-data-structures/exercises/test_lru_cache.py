import ast
import inspect
import random
import signal

import pytest

import lru_cache
from lru_cache import LRUCache


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with O(1) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something scanning every entry on each operation?")

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
    """Slow, but simple enough to check by reading it: a list of keys, least recent first."""

    def __init__(self, capacity):
        self.cap, self.order, self.vals = capacity, [], {}

    def _touch(self, k):
        self.order.remove(k)
        self.order.append(k)

    def get(self, k, default=None):
        if k not in self.vals:
            return default
        self._touch(k)
        return self.vals[k]

    def put(self, k, v):
        if k in self.vals:
            self._touch(k)
        else:
            if len(self.order) == self.cap:
                del self.vals[self.order.pop(0)]
            self.order.append(k)
        self.vals[k] = v

    def delete(self, k):
        if k not in self.vals:
            return False
        self.order.remove(k)
        del self.vals[k]
        return True


def test_example():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)
    assert c.get("b") is None
    assert c.keys() == ["a", "c"]
    assert len(c) == 2


def test_invalid_capacity():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            LRUCache(bad)


def test_capacity_one():
    c = LRUCache(1)
    c.put("x", 1)
    c.put("y", 2)
    assert c.get("x") is None and c.get("y") == 2
    assert c.keys() == ["y"] and len(c) == 1


def test_get_refreshes_and_miss_changes_nothing():
    c = LRUCache(3)
    for k in "abc":
        c.put(k, k.upper())
    assert c.get("a") == "A"
    assert c.keys() == ["b", "c", "a"]
    assert c.get("zzz") is None
    assert c.get("zzz", default=-1) == -1
    assert c.keys() == ["b", "c", "a"]
    assert len(c) == 3
    c.put("d", "D")  # evicts b, now the least recent
    assert "b" not in c and c.keys() == ["c", "a", "d"]


def test_update_refreshes_and_never_evicts():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(1, "A")  # update: no eviction, 2 is now least recent
    assert len(c) == 2 and c.keys() == [2, 1]
    c.put(3, "c")
    assert c.get(1) == "A" and c.get(2) is None
    assert c.keys() == [3, 1]


def test_peek_and_contains_do_not_touch_order():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.peek("a") == 1
    assert "a" in c and "zzz" not in c
    assert c.peek("zzz", 0) == 0
    assert c.keys() == ["a", "b"]
    c.put("c", 3)  # "a" was only peeked at, so it is still the least recent
    assert "a" not in c and c.keys() == ["b", "c"]


def test_delete_from_every_position():
    for victim in "abcd":
        c = LRUCache(4)
        for k in "abcd":
            c.put(k, k)
        assert c.delete(victim) is True
        assert c.delete(victim) is False
        rest = [k for k in "abcd" if k != victim]
        assert c.keys() == rest and len(c) == 3 and victim not in c
        c.put("e", "e")
        c.put("f", "f")  # full again: evicts the least recent survivor
        assert c.keys() == rest[1:] + ["e", "f"]
    c = LRUCache(1)
    c.put("a", 1)
    assert c.delete("a") and len(c) == 0 and c.keys() == []
    c.put("b", 2)
    assert c.keys() == ["b"]


def test_none_and_falsy_values():
    c = LRUCache(2)
    c.put("a", None)
    c.put("b", 0)
    assert "a" in c and c.get("a", "missing") is None
    assert c.get("b", "missing") == 0
    assert c.keys() == ["a", "b"]


def test_random_against_model():
    rng = random.Random(8)
    for _ in range(60):
        cap = rng.randint(1, 8)
        c, m = LRUCache(cap), Model(cap)
        for _ in range(300):
            k, op = rng.randint(0, 12), rng.random()
            if op < 0.4:
                assert c.get(k, -1) == m.get(k, -1)
            elif op < 0.85:
                v = rng.randint(0, 99)
                c.put(k, v)
                m.put(k, v)
            elif op < 0.95:
                assert c.delete(k) == m.delete(k)
            else:
                assert (k in c) == (k in m.vals)
            assert len(c) == len(m.order)
            assert c.keys() == m.order


def run_counted(cap, ops, seed):
    rng = random.Random(seed)
    c = LRUCache(cap)
    for i in range(cap):  # fill it first, so most puts evict
        c.put(K(i), i)
    K.calls = 0
    for _ in range(ops):
        k = K(rng.randrange(3 * cap))  # a fresh, equal key object: lookups really compare
        r = rng.random()
        if r < 0.5:
            c.get(k)
        elif r < 0.9:
            c.put(k, 1)
        elif r < 0.95:
            c.peek(k)
        else:
            c.delete(k)
    assert len(c) <= cap
    return K.calls


def test_hash_and_eq_calls_are_constant_per_operation():
    ops = 20_000
    calls = run_counted(2_000, ops, seed=4)
    assert calls <= 8 * ops, (
        f"{calls:,} __hash__/__eq__ calls for {ops:,} operations ({calls / ops:.0f} each, budget 8): "
        "is something searching a list of keys?"
    )


def test_cost_does_not_grow_with_capacity():
    ops = 5_000
    small, big = run_counted(100, ops, seed=6), run_counted(5_000, ops, seed=6)
    assert big <= 8 * ops and small <= 8 * ops, f"{small:,} calls at capacity 100, {big:,} at 5,000"


def test_many_operations_quickly():
    rng = random.Random(10)
    cap = 50_000
    c = LRUCache(cap)
    keys = [rng.randrange(200_000) for _ in range(300_000)]
    for i, k in enumerate(keys):
        if i % 3 == 0:
            c.get(k)
        else:
            c.put(k, i)
    assert len(c) == cap
    assert len(c.keys()) == cap


def test_evicting_from_a_big_full_cache():
    # 1,000,000 puts, 800,000 of them evictions: well under a second with a
    # linked list. Evicting with next(iter(some_dict)) has to step over every
    # slot deleted since the dict last resized: about 35 s on a machine where
    # the linked list takes 0.2 s.
    cap = 200_000
    c = LRUCache(cap)
    for i in range(5 * cap):
        c.put(i, i)
    assert len(c) == cap
    assert c.get(5 * cap - 1) == 5 * cap - 1 and c.get(4 * cap - 1) is None


def test_builds_its_own_list():
    tree = ast.parse(inspect.getsource(lru_cache))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""] + [a.name for a in node.names]
        elif isinstance(node, ast.Attribute):
            names = [node.attr]
        else:
            continue
        for n in names:
            assert n not in ("OrderedDict", "functools", "lru_cache"), f"build the linked list yourself (found {n})"
