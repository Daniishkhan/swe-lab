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
    empty_cols = make_grid(3, 0)
    assert empty_cols == [[], [], []]
    empty_cols[0].append(1)
    assert empty_cols[1] == [] and empty_cols[2] == []
    board = make_grid(2, 3, fill=".")
    assert board == [[".", ".", "."], [".", ".", "."]]
    board[1][2] = "X"
    assert board[0] == [".", ".", "."]
    with pytest.raises(ValueError):
        make_grid(-1, 2)
    with pytest.raises(ValueError):
        make_grid(2, -1)
    with pytest.raises(ValueError):
        make_grid(0, -1)


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
    # Empty list is falsy — catches buggy `bucket = bucket or []`!
    empty = []
    out_empty = append_log("first", empty)
    assert out_empty is empty
    assert empty == ["first"]


# ---------------------------------------------------------------- PriorityTask

def test_priority_task_heap_ordering_and_hashability():
    t1 = PriorityTask(2, 1, "low-a")
    t2 = PriorityTask(1, 2, "high-later")
    t3 = PriorityTask(1, 1, "high-b")
    t4 = PriorityTask(1, 1, "high-a")
    t3_dup = PriorityTask(1, 1, "high-b")

    assert (t1.priority, t1.seq, t1.name) == (2, 1, "low-a")
    assert t4 < t3 < t2 < t1
    assert t3 == t3_dup and t3 != t4
    assert hash(t3) == hash(t3_dup)
    assert len({t1, t2, t3, t4, t3_dup}) == 4
    status = {t3: "queued"}
    assert status[t3_dup] == "queued"

    heap = []
    for t in (t1, t2, t3, t4):
        heapq.heappush(heap, t)
    popped = [heapq.heappop(heap).name for _ in range(4)]
    assert popped == ["high-a", "high-b", "high-later", "low-a"]


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

    assert lookup("none") is None and lookup("none") is None
    assert lookup("false") is False and lookup("false") is False
    assert lookup("zero") == 0 and lookup("zero") == 0 and type(lookup("zero")) is int
    assert lookup("empty") == "" and lookup("empty") == ""
    assert calls == 4


def test_memoize_multi_arg_zero_arg_and_separate_caches():
    add_calls = 0
    mul_calls = 0
    const_calls = 0

    @memoize
    def add(a, b):
        nonlocal add_calls
        add_calls += 1
        return a + b

    @memoize
    def mul(a, b):
        nonlocal mul_calls
        mul_calls += 1
        return a * b

    @memoize
    def constant():
        nonlocal const_calls
        const_calls += 1
        return 42

    assert add(2, 3) == 5
    assert add(2, 3) == 5
    assert add(3, 2) == 5
    assert mul(2, 3) == 6
    assert mul(2, 3) == 6
    assert constant() == 42 and constant() == 42
    assert add_calls == 2
    assert mul_calls == 1
    assert const_calls == 1


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


def test_scoped_append_nested_backtracking():
    path = []
    with scoped_append(path, "a"):
        assert path == ["a"]
        with pytest.raises(ValueError):
            with scoped_append(path, "b"):
                assert path == ["a", "b"]
                raise ValueError("dead end")
        assert path == ["a"]
    assert path == []
