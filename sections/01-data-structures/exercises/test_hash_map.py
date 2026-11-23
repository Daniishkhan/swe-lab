import math

import pytest

from hash_map import HashMap


class Key:
    """A key that counts every == and hash() made on it (shared counters)."""

    eqs = 0
    hashes = 0
    budget = float("inf")  # a test may set this so a slow solution fails fast

    def __init__(self, v, h=None):
        self.v = v
        self.h = hash(v) if h is None else h

    def __hash__(self):
        Key.hashes += 1
        if Key.hashes > Key.budget:
            raise AssertionError(f"over {Key.budget:,} hash() calls: is every resize rehashing everything?")
        return self.h

    def __eq__(self, other):
        Key.eqs += 1
        return isinstance(other, Key) and self.v == other.v

    def __repr__(self):
        return f"Key({self.v!r})"


def reset(budget=float("inf")):
    Key.eqs = Key.hashes = 0
    Key.budget = budget


def test_put_get():
    m = HashMap()
    m.put("a", 1)
    m.put("b", 2)
    assert m.get("a") == 1
    assert m.get("b") == 2
    assert len(m) == 2


def test_overwrite_does_not_grow():
    m = HashMap()
    m.put("a", 1)
    m.put("a", 99)
    assert m.get("a") == 99
    assert len(m) == 1


def test_missing_key_raises():
    m = HashMap()
    with pytest.raises(KeyError):
        m.get("nope")
    with pytest.raises(KeyError):
        m.remove("nope")
    m.put("a", 1)
    m.remove("a")
    with pytest.raises(KeyError):
        m.remove("a")


def test_remove_and_contains():
    m = HashMap()
    m.put("a", 1)
    assert "a" in m
    assert "b" not in m
    m.remove("a")
    assert "a" not in m
    assert len(m) == 0


def test_none_is_a_valid_value():
    m = HashMap()
    m.put("k", None)
    assert "k" in m
    assert m.get("k") is None


def test_collisions_are_kept_apart():
    # Every key has hash 1: one long chain. Equality must tell them apart.
    m = HashMap()
    keys = [Key(i, h=1) for i in range(20)]
    for i, k in enumerate(keys):
        m.put(k, i)
    for i, k in enumerate(keys):
        assert m.get(k) == i
    m.remove(keys[5])
    assert keys[5] not in m
    assert m.get(keys[6]) == 6
    assert len(m) == 19


def test_equal_keys_are_the_same_key():
    m = HashMap()
    m.put(Key("x"), 1)
    m.put(Key("x"), 2)  # a different object, but equal: overwrite
    assert len(m) == 1
    assert m.get(Key("x")) == 2


def test_resizes_under_load():
    m = HashMap(initial_capacity=8, max_load_factor=0.75)
    for i in range(1000):
        m.put(i, i * i)
        assert len(m) / m.capacity <= 0.75
    assert all(m.get(i) == i * i for i in range(1000))


def test_resizes_rehash_every_key():
    # Small consecutive integers keep their bucket when the table doubles, so
    # use keys far apart. A resize that copies bucket i to bucket i loses most.
    keys = [i * 7919 for i in range(1000)]
    m = HashMap(initial_capacity=8)
    for k in keys:
        m.put(k, k)
    lost = [k for k in keys if k not in m]
    assert not lost, f"{len(lost):,} of {len(keys):,} keys lost: does a resize rehash every key into the new buckets?"


def test_no_dict_or_set_inside():
    m = HashMap()
    for i in range(50):
        m.put(i, i)
    for name, value in vars(m).items():
        assert not isinstance(value, (dict, set, frozenset)), f"self.{name} is a {type(value).__name__}"


def test_lookups_compare_few_keys():
    n = 5000
    keys = [Key(i) for i in range(n)]
    m = HashMap()
    for i, k in enumerate(keys):
        m.put(k, i)
    reset()
    for i, k in enumerate(keys):
        assert m.get(k) == i
    # With load <= 0.75 a hit compares about 1.4 keys on average. Scanning one
    # long list, or never resizing, compares thousands per lookup.
    assert Key.eqs <= 3 * n, f"{Key.eqs:,} == calls for {n:,} lookups: chains are long (is the table growing?)"
    reset()
    for i in range(n, 2 * n):
        assert Key(i) not in m
    assert Key.eqs <= 3 * n, f"{Key.eqs:,} == calls for {n:,} misses: a miss should only walk one short chain"


def test_chains_stay_short():
    # Counting == alone can't see a chain that's skipped by comparing stored
    # hashes first, so look at the chains directly.
    n = 5000
    m = HashMap()
    for i in range(n):
        m.put(i * 7919, i)
    sizes = m.bucket_sizes()
    assert len(sizes) == m.capacity
    assert sum(sizes) == n
    assert max(sizes) <= 12, f"longest chain {max(sizes):,}: keys aren't spread over the buckets"


def test_capacity_grows_by_a_multiple():
    m = HashMap(initial_capacity=8)
    caps = {m.capacity}
    n = 20_000
    limit = math.log(n / 8) / math.log(1.5) + 3  # allows growth factors from x1.5 up
    for i in range(n):
        m.put(i, i)
        caps.add(m.capacity)
        # Doubling from 8 to fit 20,000 keys takes about 12 resizes (x1.5: about 20).
        # Growing by a fixed step takes thousands, each rehashing everything: O(n^2).
        assert len(caps) <= limit, f"{len(caps) - 1} resizes after {i + 1:,} inserts: grow by a multiple"


def test_hashing_is_amortized_constant():
    n = 20_000
    keys = [Key(i) for i in range(n)]
    m = HashMap()
    # A few hashes per put, plus one per key moved in a resize (< 2n moves in
    # total when doubling). Fixed-step growth needs millions.
    reset(budget=10 * n)
    try:
        for i, k in enumerate(keys):
            m.put(k, i)
    finally:
        reset()
