import heapq

import pytest

from py_internals import PriorityTask, append_log, make_grid, memoize, scoped_append


# ---------------------------------------------------------------- make_grid

def test_make_grid_independent_rows():
    g = make_grid(3, 4, fill=0)
    assert g == [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    g[0][0] = 99
    assert g[1][0] == 0 and g[2][0] == 0


def test_make_grid_edges():
    assert make_grid(0, 5) == []
    assert make_grid(3, 0) == [[], [], []]
    with pytest.raises(ValueError):
        make_grid(-1, 2)
    with pytest.raises(ValueError):
        make_grid(2, -1)


# ---------------------------------------------------------------- append_log

def test_append_log_no_shared_default():
    a = append_log("first")
    b = append_log("second")
    assert a == ["first"]
    assert b == ["second"]
    assert a is not b


def test_append_log_existing_bucket():
    existing = ["x"]
    out = append_log("y", existing)
    assert out is existing
    assert existing == ["x", "y"]


# ---------------------------------------------------------------- PriorityTask

def test_priority_task_heap_ordering_and_hashability():
    t1 = PriorityTask(2, 1, "low-a")
    t2 = PriorityTask(1, 2, "high-later")
    t3 = PriorityTask(1, 1, "high-earlier")
    t3_dup = PriorityTask(1, 1, "high-earlier")

    assert t3 == t3_dup
    assert hash(t3) == hash(t3_dup)
    assert len({t1, t2, t3, t3_dup}) == 3

    heap = []
    for t in (t1, t2, t3):
        heapq.heappush(heap, t)
    popped = [heapq.heappop(heap).name for _ in range(3)]
    assert popped == ["high-earlier", "high-later", "low-a"]


def test_priority_task_is_immutable():
    t = PriorityTask(1, 0, "job")
    with pytest.raises((AttributeError, TypeError)):
        t.priority = 99


# ---------------------------------------------------------------- memoize

def test_memoize_caches_and_preserves_metadata():
    calls = 0

    @memoize
    def fib(n):
        """Compute nth Fibonacci number."""
        nonlocal calls
        calls += 1
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    assert fib.__name__ == "fib"
    assert fib.__doc__ == "Compute nth Fibonacci number."
    assert fib(35) == 9227465
    assert calls == 36


def test_memoize_caches_falsy_values():
    calls = 0

    @memoize
    def lookup(key):
        nonlocal calls
        calls += 1
        return {"none": None, "zero": 0, "false": False, "empty": ""}[key]

    for k, expected in [("none", None), ("zero", 0), ("false", False), ("empty", "")]:
        assert lookup(k) == expected
        assert lookup(k) == expected
    assert calls == 4


# ---------------------------------------------------------------- scoped_append

def test_scoped_append_normal_and_exception():
    path = ["root"]
    with scoped_append(path, "child") as cur:
        assert cur is path
        assert path == ["root", "child"]
    assert path == ["root"]

    with pytest.raises(RuntimeError):
        with scoped_append(path, "boom"):
            assert path == ["root", "boom"]
            raise RuntimeError("fail inside with")
    assert path == ["root"]
