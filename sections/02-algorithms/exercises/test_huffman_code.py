import math
import random
import signal
from functools import lru_cache

import pytest

from huffman_code import huffman_code


@pytest.fixture(autouse=True)
def time_limit():
    """A 10 s cap per test (the big one sets its own); Unix only."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something re-sorting or re-scanning every round?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class W:
    """A count that counts every comparison made with it (class-wide).
    Adding two counts gives another W."""

    __slots__ = ("_v",)
    cmps = 0

    def __init__(self, v):
        self._v = v

    @staticmethod
    def _u(o):
        return o._v if isinstance(o, W) else o

    def _c(self, o):
        W.cmps += 1
        return W._u(o)

    def __lt__(self, o): return self._v < self._c(o)
    def __le__(self, o): return self._v <= self._c(o)
    def __gt__(self, o): return self._v > self._c(o)
    def __ge__(self, o): return self._v >= self._c(o)
    def __eq__(self, o): return self._v == self._c(o)
    def __ne__(self, o): return self._v != self._c(o)
    def __hash__(self): return hash(self._v)
    def __add__(self, o): return W(self._v + W._u(o))
    __radd__ = __add__
    def __repr__(self): return f"W({self._v})"


# ---------------------------------------------------------------- checkers and brute force
def check_code(freqs, code, want_total):
    assert set(code) == set(freqs), f"one code word per symbol: got keys {sorted(map(str, code))}"
    words = list(code.values())
    for w in words:
        assert isinstance(w, str) and w and set(w) <= {"0", "1"}, f"code words are non-empty strings of 0 and 1, got {w!r}"
    ordered = sorted(words)
    for a, b in zip(ordered, ordered[1:]):   # a prefix sorts right before something it starts
        assert not b.startswith(a), f"{a!r} is the start of {b!r}: not prefix-free"
    total = sum(freqs[s] * len(code[s]) for s in freqs)
    assert total == want_total, f"total {total} bits, but {want_total} is possible: {freqs}"


def brute_total(counts):
    """Smallest total over every way to pair up trees: each merge adds its sum."""
    @lru_cache(maxsize=None)
    def best(ws):
        if len(ws) <= 1:
            return 0
        out = math.inf
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                rest = ws[:i] + ws[i + 1:j] + ws[j + 1:] + (ws[i] + ws[j],)
                out = min(out, ws[i] + ws[j] + best(tuple(sorted(rest))))
        return out
    if len(counts) == 1:
        return counts[0]   # one symbol, one bit per occurrence
    return best(tuple(sorted(counts)))


# ---------------------------------------------------------------- tests
def test_example():
    freqs = {"a": 45, "b": 13, "c": 12, "d": 16, "e": 9, "f": 5}
    code = huffman_code(freqs)
    check_code(freqs, code, 224)
    assert len(code["a"]) == 1


def test_tiny():
    assert huffman_code({}) == {}
    assert huffman_code({"x": 7}) == {"x": "0"}
    code = huffman_code({"x": 1, "y": 100})
    assert sorted(code.values()) == ["0", "1"]


def test_equal_counts_and_any_symbols():
    freqs = {s: 5 for s in "abcd"}
    check_code(freqs, huffman_code(freqs), 4 * 5 * 2)
    freqs = {1: 3, (2, 3): 3, "z": 3}
    check_code(freqs, huffman_code(freqs), 3 * 1 + 3 * 2 + 3 * 2)


def test_skewed_counts_make_a_chain():
    freqs = {"a": 1, "b": 1, "c": 2, "d": 4, "e": 8, "f": 16}
    code = huffman_code(freqs)
    check_code(freqs, code, 1 * 5 + 1 * 5 + 2 * 4 + 4 * 3 + 8 * 2 + 16 * 1)


def test_random_small_against_brute_force():
    rng = random.Random(70)
    for _ in range(250):
        n = rng.randint(1, 7)
        freqs = {f"s{i}": rng.randint(1, 20) for i in range(n)}
        check_code(freqs, huffman_code(freqs), brute_total(list(freqs.values())))


def test_does_not_modify_input():
    freqs = {"a": 45, "b": 13, "c": 12}
    huffman_code(freqs)
    assert freqs == {"a": 45, "b": 13, "c": 12}


def test_power_of_two_equal_counts():
    n = 2048
    freqs = {f"s{i}": 3 for i in range(n)}
    W.cmps = 0
    code = huffman_code({s: W(c) for s, c in freqs.items()})
    used = W.cmps
    check_code(freqs, code, n * 11 * 3)   # a perfect tree: 11 bits each
    budget = 12 * n * math.log2(n)
    assert used <= budget, f"{used:,} comparisons for {n:,} symbols (budget {budget:,.0f}): keep the trees in a heap"


def test_comparisons_random():
    rng = random.Random(71)
    n = 2000
    freqs = {f"s{i}": rng.randint(1, 10_000) for i in range(n)}
    W.cmps = 0
    code = huffman_code({s: W(c) for s, c in freqs.items()})
    used = W.cmps
    check_code(freqs, code, 107_158_441)   # computed offline
    budget = 12 * n * math.log2(n)
    assert used <= budget, f"{used:,} comparisons for {n:,} symbols (budget {budget:,.0f}): keep the trees in a heap"


def test_big_input_is_fast():
    """O(n log n) for real, not just in comparisons: popping from the front of a
    sorted list, or inserting near its front, moves every item after it, so it
    is O(n) per merge even though bisect needs only log n comparisons.
    The input is big so the gap is wide: a heap takes 1 to 3 s here, a sorted
    list with pop(0) or insort over 40 s."""
    n = 2 ** 19
    freqs = {i: 3 for i in range(n)}

    def boom(*_):
        raise TimeoutError("over 10 s on 524,288 symbols: is each merge O(n), like list.pop(0) or list.insert?")

    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, boom)
        signal.setitimer(signal.ITIMER_REAL, 10)
    code = huffman_code(freqs)
    if hasattr(signal, "SIGALRM"):
        signal.setitimer(signal.ITIMER_REAL, 0)
    assert len(code) == n
    assert all(len(w) == 19 for w in code.values()), "2^19 equal counts: a perfect tree, 19 bits each"
    assert len(set(code.values())) == n, "two symbols got the same code word"
