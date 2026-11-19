import pytest

from consistent_hash import ConsistentHashRing

KEYS = [f"user:{i}" for i in range(3000)]


def ring_with(*names):
    r = ConsistentHashRing(vnodes=100)
    for n in names:
        r.add_node(n)
    return r


def test_empty_ring_raises():
    with pytest.raises(LookupError):
        ConsistentHashRing().get_node("k")


def test_deterministic():
    a = ring_with("a", "b", "c")
    b = ring_with("c", "a", "b")
    assert all(a.get_node(k) == b.get_node(k) for k in KEYS)


def test_reasonably_balanced():
    r = ring_with("a", "b", "c")
    counts = {"a": 0, "b": 0, "c": 0}
    for k in KEYS:
        counts[r.get_node(k)] += 1
    for c in counts.values():
        assert 0.15 * len(KEYS) < c < 0.55 * len(KEYS)


def test_adding_node_only_moves_keys_to_new_node():
    r = ring_with("a", "b", "c")
    before = {k: r.get_node(k) for k in KEYS}
    r.add_node("d")
    moved = [k for k in KEYS if r.get_node(k) != before[k]]
    assert moved, "some keys should move to the new node"
    assert all(r.get_node(k) == "d" for k in moved)


def test_removing_node_only_moves_its_keys():
    r = ring_with("a", "b", "c")
    before = {k: r.get_node(k) for k in KEYS}
    r.remove_node("b")
    for k in KEYS:
        if before[k] != "b":
            assert r.get_node(k) == before[k]
        else:
            assert r.get_node(k) in {"a", "c"}
