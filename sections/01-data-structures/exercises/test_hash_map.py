import pytest

from hash_map import HashMap


class Collides:
    """Different objects that all share one hash value."""

    def __init__(self, name):
        self.name = name

    def __hash__(self):
        return 1

    def __eq__(self, other):
        return isinstance(other, Collides) and other.name == self.name


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


def test_remove_and_contains():
    m = HashMap()
    m.put("a", 1)
    assert "a" in m
    m.remove("a")
    assert "a" not in m
    assert len(m) == 0


def test_collisions_are_kept_apart():
    m = HashMap()
    keys = [Collides(i) for i in range(20)]
    for i, k in enumerate(keys):
        m.put(k, i)
    for i, k in enumerate(keys):
        assert m.get(k) == i
    m.remove(keys[5])
    assert keys[5] not in m
    assert m.get(keys[6]) == 6


def test_resizes_under_load():
    m = HashMap(initial_capacity=8, max_load_factor=0.75)
    for i in range(1000):
        m.put(i, i * i)
    assert len(m) == 1000
    assert len(m) / m.capacity <= 0.75
    assert all(m.get(i) == i * i for i in range(1000))


def test_none_is_a_valid_value():
    m = HashMap()
    m.put("k", None)
    assert "k" in m
    assert m.get("k") is None
