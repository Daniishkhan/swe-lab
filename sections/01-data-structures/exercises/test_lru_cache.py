import pytest

from lru_cache import LRUCache


def test_invalid_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)


def test_basic_eviction():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(3, "c")  # evicts 1
    assert c.get(1) is None
    assert c.get(2) == "b"
    assert c.get(3) == "c"
    assert len(c) == 2


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.get(1)  # 2 is now least recent
    c.put(3, "c")
    assert c.get(2) is None
    assert c.get(1) == "a"


def test_put_update_refreshes_recency():
    c = LRUCache(2)
    c.put(1, "a")
    c.put(2, "b")
    c.put(1, "A")  # update, 2 is now least recent
    c.put(3, "c")
    assert c.get(1) == "A"
    assert c.get(2) is None
    assert len(c) == 2


def test_capacity_one():
    c = LRUCache(1)
    c.put("x", 1)
    c.put("y", 2)
    assert c.get("x") is None
    assert c.get("y") == 2


def test_default():
    c = LRUCache(1)
    assert c.get("missing", default=-1) == -1
