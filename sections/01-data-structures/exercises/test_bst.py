import inspect
import random
import re
import signal
from bisect import bisect_left, bisect_right

import pytest

import bst as bst_module
from bst import BST


@pytest.fixture(autouse=True)
def time_limit():
    """Every test runs in well under a second with O(height) operations
    (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something walking the whole tree on every call?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class K:
    """A key that counts every comparison made with it (class-wide)."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        K.cmps += 1
        return other.v if isinstance(other, K) else other

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __eq__(self, o): return self.v == self._o(o)
    def __ne__(self, o): return self.v != self._o(o)
    def __hash__(self): raise TypeError("the tree must compare keys, not hash them")
    def __repr__(self): return f"K({self.v})"


def middle_first(lo, hi, out):
    """Insert order lo..hi that builds a perfectly balanced tree."""
    stack = [(lo, hi)]
    while stack:
        a, b = stack.pop()
        if a > b:
            continue
        m = (a + b) // 2
        out.append(m)
        stack.append((m + 1, b))
        stack.append((a, m - 1))
    return out


H = 14
N = 2 ** H - 1  # 16,383 keys, perfectly balanced: height 14


def balanced_tree():
    """Keys 0, 2, 4, ..., 2(N-1), so odd numbers fall between keys."""
    t = BST()
    for i in middle_first(0, N - 1, []):
        t.insert(K(2 * i))
    return t


def values(it):
    return [k.v if isinstance(k, K) else k for k in it]


def test_example():
    t = BST()
    for k in [50, 30, 70, 20, 40, 60, 80]:
        assert t.insert(k) is True
    assert t.insert(40) is False
    assert len(t) == 7 and list(t) == [20, 30, 40, 50, 60, 70, 80]
    assert t.successor(50) == 60 and t.successor(45) == 50 and t.successor(80) is None and t.successor(1) == 20
    assert t.range(25, 65) == [30, 40, 50, 60]
    assert t.range(50, 50) == [] and t.range(0, 100) == [20, 30, 40, 50, 60, 70, 80] and t.range(81, 90) == []
    assert (t.min(), t.max(), t.height()) == (20, 80, 3)
    t.delete(50)
    assert list(t) == [20, 30, 40, 60, 70, 80] and 50 not in t and 60 in t and len(t) == 6


def test_empty_and_single():
    t = BST()
    assert len(t) == 0 and list(t) == [] and t.height() == 0
    assert 5 not in t and t.successor(5) is None and t.range(0, 9) == []
    with pytest.raises(ValueError):
        t.min()
    with pytest.raises(ValueError):
        t.max()
    with pytest.raises(KeyError):
        t.delete(5)
    t.insert(5)
    assert t.height() == 1 and t.min() == t.max() == 5
    t.delete(5)
    assert len(t) == 0 and t.height() == 0 and list(t) == []


def test_delete_all_three_cases():
    t = BST()
    for k in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
        t.insert(k)
    t.delete(14)  # one child
    assert list(t) == [1, 3, 4, 6, 7, 8, 10, 13]
    t.delete(3)  # two children
    assert list(t) == [1, 4, 6, 7, 8, 10, 13]
    t.delete(8)  # two children, at the root
    assert list(t) == [1, 4, 6, 7, 10, 13]
    t.delete(1)  # leaf
    assert list(t) == [4, 6, 7, 10, 13] and len(t) == 5
    with pytest.raises(KeyError):
        t.delete(8)
    for k in [4, 6, 7, 10, 13]:
        t.delete(k)
    assert len(t) == 0 and list(t) == []


def test_matches_sorted_reference():
    rng = random.Random(31)
    for trial in range(30):
        t, ref = BST(), []
        for _ in range(300):
            k = rng.randint(0, 60)
            op = rng.random()
            if op < 0.5:
                added = t.insert(k)
                assert added == (k not in ref)
                if added:
                    ref.insert(bisect_left(ref, k), k)
            elif op < 0.8:
                if k in ref:
                    t.delete(k)
                    ref.remove(k)
                else:
                    with pytest.raises(KeyError):
                        t.delete(k)
            else:
                assert (k in t) == (k in ref)
                i = bisect_right(ref, k)
                assert t.successor(k) == (ref[i] if i < len(ref) else None)
                lo, hi = sorted((k, rng.randint(0, 60)))
                assert t.range(lo, hi) == ref[bisect_left(ref, lo):bisect_left(ref, hi)]
            assert len(t) == len(ref)
        assert list(t) == ref, trial
        if ref:
            assert (t.min(), t.max()) == (ref[0], ref[-1])


def test_sorted_inserts_make_a_chain():
    t = BST()
    for k in range(1, 501):
        t.insert(k)
    assert t.height() == 500, "a plain BST built from sorted keys is a 500-level chain"
    t2 = BST()
    for k in middle_first(1, 15, []):
        t2.insert(k)
    assert t2.height() == 4


def test_search_is_about_one_comparison_per_level():
    t = balanced_tree()
    assert t.height() == H
    rng = random.Random(2)
    probes = [K(rng.randrange(2 * N)) for _ in range(2_000)]  # half present, half between keys
    K.cmps = 0
    for p in probes:
        assert (p in t) == (p.v % 2 == 0)
    per = K.cmps / len(probes)
    assert per <= 3 * H, f"{per:.0f} comparisons per search in a tree of height {H}: is the search walking more than one path?"


def test_min_max_walk_one_path():
    t = balanced_tree()
    K.cmps = 0
    assert t.min().v == 0 and t.max().v == 2 * (N - 1)
    assert K.cmps <= 2 * H, f"{K.cmps} comparisons for min and max: they should only walk down one side"


def test_successor_walks_one_path():
    t = balanced_tree()
    rng = random.Random(5)
    probes = [K(rng.randrange(-1, 2 * N)) for _ in range(2_000)]
    K.cmps = 0
    got = [t.successor(p) for p in probes]
    per = K.cmps / len(probes)
    for p, s in zip(probes, got):
        want = p.v + 1 if p.v % 2 else p.v + 2  # the next even number
        assert (s.v if s is not None else None) == (want if want <= 2 * (N - 1) else None), p
    assert per <= 3 * H, f"{per:.0f} comparisons per successor: is it scanning in order instead of walking down?"


def test_range_costs_height_plus_output():
    t = balanced_tree()
    rng = random.Random(8)
    total_out, queries = 0, []
    for _ in range(300):
        lo = rng.randrange(2 * N)
        queries.append((K(lo), K(lo + rng.randint(0, 40))))
    K.cmps = 0
    for lo, hi in queries:
        got = values(t.range(lo, hi))
        first = lo.v + lo.v % 2
        assert got == list(range(first, min(hi.v, 2 * N - 1), 2)), (lo, hi)
        total_out += len(got)
    budget = 300 * 6 * (H + 1) + 4 * total_out
    assert K.cmps <= budget, f"{K.cmps:,} comparisons for 300 small ranges (budget {budget:,}): does range skip subtrees outside [lo, hi)?"


def test_delete_costs_one_path():
    t = balanced_tree()
    rng = random.Random(13)
    victims = rng.sample(range(N), 3_000)
    K.cmps = 0
    for i in victims:
        t.delete(K(2 * i))
    per = K.cmps / len(victims)
    assert per <= 4 * H, f"{per:.0f} comparisons per delete: finding the successor needs no comparisons, just walking left"
    assert len(t) == N - 3_000
    left = sorted(set(range(N)) - set(victims))
    assert values(t) == [2 * i for i in left]


def test_the_tree_does_the_work():
    """Comparisons can't see a hidden sorted list (bisect and list.insert do
    their work in C), so check the source for the usual shortcuts."""
    src = inspect.getsource(bst_module)
    src = re.sub(r'""".*?"""', "", src, flags=re.S)  # ignore docstrings
    for banned in ("bisect", "sorted(", ".sort(", "SortedList", "dict(", "set("):
        assert banned not in src, f"bst.py uses {banned!r}: the tree itself must keep the order"
