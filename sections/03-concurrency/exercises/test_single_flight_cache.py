import threading
import time

import pytest

from single_flight_cache import SingleFlightCache


def test_lru_eviction_and_falsy_values():
    with pytest.raises(ValueError):
        SingleFlightCache(0)

    c = SingleFlightCache(2)
    calls = {"a": 0, "b": 0, "c": 0, "z": 0}

    def load(k, val):
        def _fn():
            calls[k] += 1
            return val
        return _fn

    assert c.get_or_load("z", load("z", 0)) == 0
    assert c.get_or_load("z", load("z", 0)) == 0
    assert calls["z"] == 1  # falsy 0 must stay cached

    assert c.get_or_load("a", load("a", "A")) == "A"
    # Touch "z" so "a" becomes LRU
    assert c.get_or_load("z", load("z", 0)) == 0
    assert c.get_or_load("b", load("b", "B")) == "B"
    assert len(c) == 2
    # "a" was evicted; loading it again must call loader
    assert c.get_or_load("a", load("a", "A2")) == "A2"
    assert calls["a"] == 2


def test_stampede_coalesces_to_single_load():
    c = SingleFlightCache(10)
    load_count = 0
    count_lock = threading.Lock()
    barrier = threading.Barrier(30)
    results = []
    res_lock = threading.Lock()

    def slow_loader():
        nonlocal load_count
        with count_lock:
            load_count += 1
        time.sleep(0.08)
        return "hot-value"

    def worker():
        barrier.wait()
        val = c.get_or_load("same-key", slow_loader)
        with res_lock:
            results.append(val)

    threads = [threading.Thread(target=worker) for _ in range(30)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3.0)
        assert not t.is_alive()

    assert load_count == 1, f"expected 1 loader call, saw {load_count}"
    assert results == ["hot-value"] * 30


def test_different_keys_load_in_parallel_without_holding_global_lock():
    c = SingleFlightCache(10)
    entered = threading.Barrier(2, timeout=1.5)

    def slow_a():
        entered.wait()  # deadlocks if cache lock is held across loader()!
        return "A"

    def slow_b():
        entered.wait()
        return "B"

    out = {}
    t1 = threading.Thread(target=lambda: out.__setitem__("a", c.get_or_load("a", slow_a)))
    t2 = threading.Thread(target=lambda: out.__setitem__("b", c.get_or_load("b", slow_b)))
    t1.start()
    t2.start()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)
    assert out == {"a": "A", "b": "B"}, "loads for distinct keys were serialized!"


def test_failed_load_propagates_and_allows_retry():
    c = SingleFlightCache(5)
    barrier = threading.Barrier(5)
    errors = []
    err_lock = threading.Lock()

    def failing_loader():
        time.sleep(0.05)
        raise RuntimeError("upstream down")

    def worker():
        barrier.wait()
        try:
            c.get_or_load("flaky", failing_loader)
        except RuntimeError as e:
            with err_lock:
                errors.append(str(e))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2.0)
        assert not t.is_alive()

    assert len(errors) == 5
    assert len(c) == 0
    # Retry after failure succeeds cleanly
    assert c.get_or_load("flaky", lambda: "recovered") == "recovered"
