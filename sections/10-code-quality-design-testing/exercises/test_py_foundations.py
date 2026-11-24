import signal
from contextlib import contextmanager

import pytest

from py_foundations import (
    countdown_evens,
    dedupe_preserve_order,
    first_negative_coords,
    tag_diff,
    word_positions,
)


@contextmanager
def cap(seconds, hint):
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(f"over {seconds} s: {hint}")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class _Tracked:
    """Hashable, comparable wrapper that counts equality comparisons."""

    def __init__(self, value, counter):
        self.value = value
        self._counter = counter

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        self._counter[0] += 1
        return isinstance(other, _Tracked) and self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __repr__(self):
        return f"T({self.value!r})"


# ---------------------------------------------------------------- countdown_evens

def test_countdown_evens_examples():
    assert countdown_evens(6) == [6, 4, 2, 0]
    assert countdown_evens(5) == [4, 2, 0]
    assert countdown_evens(0) == [0]
    assert countdown_evens(1) == [0]


def test_countdown_evens_rejects_negative():
    with pytest.raises(ValueError):
        countdown_evens(-1)
    with pytest.raises(ValueError):
        countdown_evens(-10)


# ---------------------------------------------------------------- first_negative_coords

def test_first_negative_coords_example_and_order():
    assert first_negative_coords([[1, 2], [0, -5, -1]]) == (1, 1)
    assert first_negative_coords([[1, -2], [-3, 4]]) == (0, 1)
    assert first_negative_coords([[-9]]) == (0, 0)


def test_first_negative_coords_edges():
    assert first_negative_coords([]) is None
    assert first_negative_coords([[], [], []]) is None
    assert first_negative_coords([[0, 1, 2], [3, 4]]) is None
    assert first_negative_coords([[], [5, 0], [1, 2, -3]]) == (2, 2)


# ---------------------------------------------------------------- dedupe_preserve_order

def test_dedupe_preserve_order_examples_and_types():
    src = ["b", "a", "b", "c", "a"]
    snapshot = list(src)
    assert dedupe_preserve_order(src) == ["b", "a", "c"]
    assert src == snapshot
    assert dedupe_preserve_order([]) == []
    assert dedupe_preserve_order([0, "", None, 0, "", None]) == [0, "", None]
    assert dedupe_preserve_order((x for x in [3, 1, 3, 2, 1])) == [3, 1, 2]
    assert dedupe_preserve_order([(0, 1), (0, 1), (1, 0)]) == [(0, 1), (1, 0)]


def test_dedupe_preserve_order_is_linear_not_quadratic():
    eq_calls = [0]
    n = 600
    items = [_Tracked(i, eq_calls) for i in range(n)]
    out = dedupe_preserve_order(items)
    assert [x.value for x in out] == list(range(n))
    # O(n^2) `if x not in out:` performs n*(n-1)/2 = 179,700 __eq__ calls;
    # O(n) set/dict lookup performs near 0 __eq__ calls on distinct hashes.
    assert eq_calls[0] <= 4 * n, (
        f"dedupe_preserve_order made {eq_calls[0]} equality checks for n={n}; "
        "use a helper set (O(n)) instead of `if x not in out:` (O(n^2))"
    )


# ---------------------------------------------------------------- word_positions

def test_word_positions_example_and_edges():
    assert word_positions("Go dog go") == {"go": [0, 2], "dog": [1]}
    assert word_positions("") == {}
    assert word_positions("   \t\n  ") == {}
    assert word_positions("A  b\tA\nB  a") == {"a": [0, 2, 4], "b": [1, 3]}


def test_word_positions_linear_on_large_input():
    n = 15_000
    text = " ".join(f"w{i}" for i in range(n))
    with cap(2, "word_positions took too long — build the dict in one O(n) pass"):
        res = word_positions(text)
    assert len(res) == n
    assert res["w0"] == [0]
    assert res[f"w{n - 1}"] == [n - 1]
    # Repeated word catches O(n^2) `positions[w] = positions.get(w, []) + [i]` list copying
    m = 35_000
    rep = " ".join(["go"] * m)
    with cap(2, "word_positions copied the index list on every match — use .append(i) in place"):
        rep_res = word_positions(rep)
    assert rep_res == {"go": list(range(m))}


# ---------------------------------------------------------------- tag_diff

def test_tag_diff_example_and_edges():
    assert tag_diff(["a", "b", "c"], ["b", "c", "d"]) == (["d"], ["a"], ["b", "c"])
    assert tag_diff([], []) == ([], [], [])
    assert tag_diff(["x", "x"], ["x", "y", "y"]) == (["y"], [], ["x"])
    # Single-use generators must work cleanly
    cur_gen = (t for t in ["c", "a", "b"])
    tgt_gen = (t for t in ["d", "b"])
    assert tag_diff(cur_gen, tgt_gen) == (["d"], ["a", "c"], ["b"])


def test_tag_diff_uses_set_algebra_not_quadratic_scans():
    eq_calls = [0]
    n = 600
    cur = [_Tracked(f"k{i:04d}", eq_calls) for i in range(0, n)]
    tgt = [_Tracked(f"k{i:04d}", eq_calls) for i in range(n // 2, n + n // 2)]
    to_add, to_remove, kept = tag_diff(cur, tgt)
    assert len(to_add) == n // 2
    assert len(to_remove) == n // 2
    assert len(kept) == n // 2
    assert to_add[0].value == f"k{n:04d}"
    assert to_remove[0].value == "k0000"
    assert kept[0].value == f"k{n // 2:04d}"
    # O(n * m) list scans perform ~360,000+ __eq__ calls; set algebra does O(n + m).
    assert eq_calls[0] <= 10 * n, (
        f"tag_diff made {eq_calls[0]} equality checks for n={n}; "
        "convert both inputs to sets and use &, - (O(n + m)) instead of list scans"
    )
