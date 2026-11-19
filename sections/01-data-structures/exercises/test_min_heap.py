import math
import random
import signal

import pytest

from min_heap import MinHeap


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with O(log n) operations (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is push or pop scanning or sorting the whole list?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class C:
    """A value that counts every comparison made with it (class-wide)."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        C.cmps += 1
        return other.v

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __repr__(self): return f"C({self.v})"


def drain(h):
    out = []
    while len(h):
        out.append(h.pop())
    return out


def test_example():
    h = MinHeap()
    for x in [5, 3, 8, 1]:
        h.push(x)
    assert h.peek() == 1 and len(h) == 4
    assert h.pop() == 1 and h.pop() == 3 and len(h) == 2
    assert MinHeap.from_list([9, 4, 7, 1]).pop() == 1


def test_push_pop_sorted():
    rng = random.Random(7)
    data = [rng.randint(-100, 100) for _ in range(500)]
    h = MinHeap()
    for x in data:
        h.push(x)
    assert len(h) == 500
    assert drain(h) == sorted(data)


def test_peek_does_not_remove():
    h = MinHeap()
    h.push(5)
    h.push(1)
    assert h.peek() == 1
    assert len(h) == 2


def test_empty_raises():
    h = MinHeap()
    with pytest.raises(IndexError):
        h.pop()
    with pytest.raises(IndexError):
        h.peek()
    h.push(3)
    h.pop()
    with pytest.raises(IndexError):
        h.pop()


def test_from_list():
    data = [9, 4, 7, 1, 8, 2, 2, 6]
    h = MinHeap.from_list(data)
    assert data == [9, 4, 7, 1, 8, 2, 2, 6], "from_list must not change the caller's list"
    assert drain(h) == sorted(data)
    assert len(MinHeap.from_list([])) == 0
    assert drain(MinHeap.from_list(iter([3, 1, 2]))) == [1, 2, 3]


def test_mixed_operations_match_sorted():
    rng = random.Random(11)
    for _ in range(50):
        start = [rng.randint(0, 50) for _ in range(rng.randint(0, 30))]
        h, ref = MinHeap.from_list(start), sorted(start)
        for _ in range(200):
            if ref and rng.random() < 0.4:
                assert h.pop() == ref.pop(0)
            else:
                x = rng.randint(0, 50)
                h.push(x)
                ref.append(x)
                ref.sort()
            assert len(h) == len(ref)
            if ref:
                assert h.peek() == ref[0]


def test_strings_and_duplicates():
    words = ["pear", "apple", "fig", "apple", "kiwi", "fig"]
    assert drain(MinHeap.from_list(words)) == sorted(words)


def test_push_costs_log_n():
    n = 4096
    h = MinHeap()
    items = [C(v) for v in range(n, 0, -1)]  # falling: every push goes all the way up
    C.cmps = 0
    for x in items:
        h.push(x)
    budget = n * math.log2(n) + 2 * n
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} pushes (budget {budget:,.0f}): does push walk more than one path?"


def test_pop_costs_log_n():
    n = 4096
    rng = random.Random(3)
    vals = rng.sample(range(10 * n), n)
    h = MinHeap()
    for v in vals:
        h.push(C(v))
    C.cmps = 0
    out = [x.v for x in drain(h)]
    assert out == sorted(vals)
    budget = 3 * n * math.log2(n)
    assert C.cmps <= budget, f"{C.cmps:,} comparisons for {n:,} pops (budget {budget:,.0f}): is pop scanning for the minimum?"


@pytest.mark.parametrize("shape", ["random", "falling"])
def test_from_list_is_linear(shape):
    n = 2 ** 15
    vals = random.Random(5).sample(range(10 * n), n) if shape == "random" else list(range(n, 0, -1))
    items = [C(v) for v in vals]
    C.cmps = 0
    h = MinHeap.from_list(items)
    built = C.cmps
    assert len(h) == n
    assert built < 3 * n, f"{built:,} comparisons to build a heap of {n:,} ({built / n:.1f} per item): heapify bottom-up is under 2 per item"
    assert h.pop().v == min(vals)
    assert [h.pop().v for _ in range(100)] == sorted(vals)[1:101]


def test_many_ints_quickly():
    # 100,000 pushes and pops of plain ints: well under a second when each one
    # walks one path, minutes if push or pop copies the whole list.
    rng = random.Random(12)
    vals = [rng.randrange(10 ** 9) for _ in range(100_000)]
    h = MinHeap()
    for v in vals:
        h.push(v)
    assert len(h) == len(vals)
    assert drain(h) == sorted(vals)
