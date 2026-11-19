import random
import signal

import pytest

from probing_map import ProbingMap


@pytest.fixture(autouse=True)
def time_limit():
    """Fail instead of hanging when a search never meets an empty slot (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("took too long: does every search end at an empty slot?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Key:
    """A key with a chosen hash, so tests control exactly where it lands."""

    def __init__(self, name, h):
        self.name, self.h = name, h

    def __hash__(self):
        return self.h

    def __eq__(self, other):
        return isinstance(other, Key) and self.name == other.name

    def __repr__(self):
        return f"Key({self.name!r}, h={self.h})"


def test_put_get_overwrite():
    m = ProbingMap()
    m.put("a", 1)
    m.put("b", 2)
    m.put("a", 3)
    assert m.get("a") == 3
    assert m.get("b") == 2
    assert len(m) == 2


def test_missing_key_raises():
    m = ProbingMap()
    with pytest.raises(KeyError):
        m.get("nope")
    with pytest.raises(KeyError):
        m.remove("nope")
    m.put("a", 1)
    m.remove("a")
    with pytest.raises(KeyError):
        m.get("a")
    with pytest.raises(KeyError):
        m.remove("a")


def test_none_is_a_valid_value():
    m = ProbingMap()
    m.put("k", None)
    assert "k" in m
    assert m.get("k") is None


def test_collisions_walk_forward_and_wrap():
    m = ProbingMap(initial_capacity=8)
    # All three want slot 7, so two of them must wrap around to slots 0 and 1.
    keys = [Key(c, 7) for c in "xyz"]
    for i, k in enumerate(keys):
        m.put(k, i)
    for i, k in enumerate(keys):
        assert m.get(k) == i


def test_delete_does_not_hide_later_keys():
    m = ProbingMap(initial_capacity=16)
    a, b, c = Key("a", 3), Key("b", 3), Key("c", 3)  # slots 3, 4, 5
    for k in (a, b, c):
        m.put(k, k.name)
    m.remove(b)  # slot 4 must become a tombstone, not empty
    assert b not in m
    assert m.get(c) == "c"
    assert m.get(a) == "a"
    m.remove(a)
    assert m.get(c) == "c"
    assert len(m) == 1


def test_overwrite_after_delete_is_still_one_entry():
    m = ProbingMap(initial_capacity=16)
    a, b = Key("a", 3), Key("b", 3)
    m.put(a, 1)
    m.put(b, 2)  # slot 4
    m.remove(a)  # slot 3 is now a tombstone
    m.put(b, 3)  # b is still in slot 4: overwrite it, don't add a second copy in slot 3
    assert len(m) == 1
    assert m.get(b) == 3
    m.remove(b)
    assert b not in m


def test_matches_a_dict_on_random_operations():
    rng = random.Random(42)
    m, ref = ProbingMap(), {}
    for _ in range(5000):
        name = rng.randrange(60)
        k = Key(name, name % 8)  # only 8 distinct hashes: lots of collisions
        op = rng.random()
        if op < 0.5:
            v = rng.random()
            m.put(k, v)
            ref[k.name] = v
        elif op < 0.8:
            if k.name in ref:
                m.remove(k)
                del ref[k.name]
            else:
                with pytest.raises(KeyError):
                    m.remove(k)
        else:
            assert (k in m) == (k.name in ref)
            if k.name in ref:
                assert m.get(k) == ref[k.name]
        assert len(m) == len(ref)


def test_churn_does_not_clog_or_bloat():
    m = ProbingMap(initial_capacity=8)
    for i in range(10_000):
        m.put(i, i)
        m.remove(i)
    # Never more than one live key, so the table has no reason to grow...
    assert m.capacity <= 16, f"capacity {m.capacity:,} with 0 live keys: rebuilds should size for live keys"
    # ...and misses must still end quickly at an empty slot.
    before = m.probes
    for i in range(10_000, 11_000):
        assert i not in m
    per = (m.probes - before) / 1000
    assert per <= 4, f"{per:.1f} probes per miss: tombstones are piling up"


def test_lookups_use_few_probes():
    n = 5000
    m = ProbingMap()
    for i in range(n):
        m.put(i * 7919, i)  # spread-out ints
    assert len(m) / m.capacity <= 0.5
    before = m.probes
    for i in range(n):
        assert m.get(i * 7919) == i
    per = (m.probes - before) / n
    # At load <= 0.5 a hit averages about 1.5 probes. Ignoring the hash and
    # scanning from slot 0 averages thousands.
    assert 1 <= per <= 4, f"{per:.1f} probes per lookup"


def test_inserts_are_amortized_constant():
    n = 20_000
    m = ProbingMap()
    before = m.probes
    # Includes the re-inserts done by every rebuild. Doubling keeps the total
    # linear; growing by a fixed step makes it quadratic.
    for i in range(n):
        m.put(i * 7919, i)
        assert m.probes - before <= 10 * n, f"over {10 * n:,} probes after {i + 1:,} inserts, rebuilds included"
