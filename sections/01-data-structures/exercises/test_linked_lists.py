import random
import signal
import tracemalloc

import pytest

from linked_lists import has_cycle, middle, reverse


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second with O(n) code. Fail instead of
    hanging if a cycle check walks a loop forever (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: does a loop in the list make your code walk forever?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class N:
    """A node that counts every read of `.next` (class-wide) and has no
    room for extra attributes, so the tests see how far your code walks."""

    __slots__ = ("val", "_next")
    reads = 0

    def __init__(self, val, nxt=None):
        self.val = val
        self._next = nxt

    @property
    def next(self):
        N.reads += 1
        return self._next

    @next.setter
    def next(self, value):
        self._next = value


def build(values):
    nodes = [N(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a._next = b
    return nodes


def to_list(head, limit=1_000_000):
    out = []
    while head is not None:
        out.append(head.val)
        head = head._next
        assert len(out) <= limit, "the list never ends: did reverse leave a loop?"
    return out


def measure(fn, *args):
    """Run fn, return (result, .next reads, peak bytes allocated during the call)."""
    N.reads = 0
    tracemalloc.start()
    try:
        result = fn(*args)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return result, N.reads, peak


# Peak memory budget for "O(1) extra memory". A list or set of 200,000 nodes
# needs well over 1 MB; a handful of variables needs a few hundred bytes.
SMALL = 64 * 1024


# 1. reverse
def test_reverse_small():
    assert reverse(None) is None
    one = build([7])
    assert reverse(one[0]) is one[0] and one[0]._next is None
    nodes = build([1, 2, 3, 4, 5])
    head = reverse(nodes[0])
    assert head is nodes[-1]
    assert to_list(head) == [5, 4, 3, 2, 1]
    assert nodes[0]._next is None, "the old head is now the tail and must point to None"


def test_reverse_twice_restores():
    nodes = build(range(10))
    head = reverse(reverse(nodes[0]))
    assert head is nodes[0] and to_list(head) == list(range(10))


def test_reverse_big_in_place():
    n = 200_000
    nodes = build(range(n))
    head, reads, peak = measure(reverse, nodes[0])
    assert head is nodes[-1], "reverse must return the old tail, the same node object"
    walk, i = head, n - 1
    while walk is not None:  # same objects, in reverse order
        assert walk is nodes[i], f"node at position {n - 1 - i} is not the original node object"
        walk, i = walk._next, i - 1
    assert i == -1
    assert reads <= 2 * n, f"{reads:,} reads of .next for {n:,} nodes: each node needs about one"
    assert peak <= SMALL, f"reverse allocated {peak:,} bytes: is there a list of nodes or a new list?"


# 2. middle
def test_middle_small():
    assert middle(None) is None
    for size in range(1, 12):
        nodes = build(range(size))
        assert middle(nodes[0]) is nodes[size // 2], f"wrong middle for {size} nodes"
        assert to_list(nodes[0]) == list(range(size)), "middle must not change the list"


def test_middle_big():
    n = 200_001
    nodes = build(range(n))
    mid, reads, peak = measure(middle, nodes[0])
    assert mid is nodes[n // 2]
    assert reads <= 3 * n, f"{reads:,} reads of .next for {n:,} nodes"
    assert peak <= SMALL, f"middle allocated {peak:,} bytes: is there a list of nodes?"


# 3. has_cycle
def test_has_cycle_small():
    assert has_cycle(None) is False
    one = build([1])
    assert has_cycle(one[0]) is False
    one[0]._next = one[0]
    assert has_cycle(one[0]) is True  # a node pointing to itself
    assert one[0].val == 1 and one[0]._next is one[0]
    # Duplicate values must not fool a cycle check comparing .val instead of node identity (`is`)
    for vals in ([5, 5], [1, 1, 1, 1], [2, 3, 2, 3, 2]):
        dup = build(vals)
        assert has_cycle(dup[0]) is False
        assert_unchanged(dup, None, vals)
    for size in range(2, 10):
        for back_to in range(size):
            vals = list(range(size))
            nodes = build(vals)
            N.reads = 0
            assert has_cycle(nodes[0]) is False
            nodes[-1]._next = nodes[back_to]
            assert has_cycle(nodes[0]) is True, f"missed a loop from node {size - 1} back to node {back_to}"
            assert N.reads <= 12 * size + 10, f"{N.reads} reads of .next for two {size}-node lists: is it walking a fixed number of steps?"
            assert_unchanged(nodes, back_to, vals)


def assert_unchanged(nodes, back_to, expected_vals=None):
    for i, node in enumerate(nodes[:-1]):
        assert node._next is nodes[i + 1], "has_cycle must not change the list"
        if expected_vals is not None:
            assert node.val == expected_vals[i], "has_cycle must not mutate node values"
    assert nodes[-1]._next is (None if back_to is None else nodes[back_to]), "has_cycle must not change the list"
    if expected_vals is not None:
        assert nodes[-1].val == expected_vals[-1], "has_cycle must not mutate node values"


@pytest.mark.parametrize("back_to", [None, 0, 100_000, 199_999])
def test_has_cycle_big_constant_memory(back_to):
    n = 200_000
    nodes = build(range(n))
    if back_to is not None:
        nodes[-1]._next = nodes[back_to]
    found, reads, peak = measure(has_cycle, nodes[0])
    assert found is (back_to is not None)
    assert reads <= 6 * n, f"{reads:,} reads of .next for {n:,} nodes: is something walking the list more than a few times?"
    assert peak <= SMALL, f"has_cycle allocated {peak:,} bytes: a set of seen nodes is O(n) memory"
    assert_unchanged(nodes, back_to, range(n))


def test_has_cycle_random_shapes():
    rng = random.Random(4)
    for _ in range(200):
        size = rng.randint(1, 40)
        vals = list(range(size))
        nodes = build(vals)
        loop = rng.random() < 0.5
        if loop:
            nodes[-1]._next = nodes[rng.randrange(size)]
        back_to = None
        if loop:
            back_to = nodes.index(nodes[-1]._next)
        N.reads = 0
        assert has_cycle(nodes[0]) is loop
        assert N.reads <= 6 * size + 10
        assert_unchanged(nodes, back_to, vals)
