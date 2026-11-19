import copy
import random
import signal
from collections.abc import Sequence

import pytest

from graph_basics import find_judge, to_csr, transpose


@pytest.fixture(autouse=True)
def time_limit():
    """O(V + E) solutions finish each test in about a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is something scanning every edge once per vertex, or copying a growing list?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class TooManyReads(Exception):
    pass


class CountingList(Sequence):
    """A read-only list that counts reads and gives up past a budget."""

    def __init__(self, items, budget):
        self._items = list(items)
        self.reads = 0
        self.budget = budget

    def _tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooManyReads(f"over {self.budget:,} reads of {len(self._items):,} trust pairs: is each person checked against every pair?")

    def __getitem__(self, i):
        if isinstance(i, slice):
            out = CountingList(self._items[i], 0)
            self._tick(len(out._items))
            out.reads, out.budget = 0, float("inf")
            out._tick = self._tick  # slices share this list's budget
            return out
        self._tick()
        return self._items[i]

    def __iter__(self):
        for x in self._items:
            self._tick()
            yield x

    def __len__(self):
        return len(self._items)


def counting(pairs):
    return CountingList(pairs, 2 * len(pairs) + 10)


def random_graph(rng, n, m):
    return [[rng.randrange(n) for _ in range(rng.randint(0, m))] for _ in range(n)]


# Brute forces: slow on purpose, used only on small inputs.
def brute_transpose(adj):
    n = len(adj)
    return [[u for u in range(n) for x in adj[u] if x == v] for v in range(n)]


def brute_judge(n, trust):
    for j in range(n):
        if all(a != j for a, _ in trust) and sum(1 for _, b in trust if b == j) == n - 1:
            return j
    return -1


# 1. transpose
def test_transpose_examples():
    assert transpose([[1, 2], [2], []]) == [[], [0], [0, 1]]
    assert transpose([]) == []
    assert transpose([[]]) == [[]]
    assert transpose([[0]]) == [[0]]  # a self-loop stays
    assert transpose([[1, 1], []]) == [[], [0, 0]]  # parallel edges stay


def test_transpose_random_and_leaves_input_alone():
    rng = random.Random(1)
    for _ in range(300):
        adj = random_graph(rng, rng.randint(0, 12), 4)
        before = copy.deepcopy(adj)
        got = transpose(adj)
        assert adj == before, "transpose must not change adj"
        assert got == brute_transpose(adj), adj
        assert all(got[v] is not adj[v] for v in range(len(adj))), "return new lists"


def test_transpose_big():
    n, offsets = 200_000, (1, 2, 3, 5, 8)  # 1,000,000 edges
    adj = [[(u + d) % n for d in offsets] for u in range(n)]
    got = transpose(adj)
    assert len(got) == n
    for v in range(0, n, 7):
        assert got[v] == sorted((v - d) % n for d in offsets), v


# 2. find_judge
def test_judge_examples():
    assert find_judge(3, counting([(0, 2), (1, 2)])) == 2
    assert find_judge(3, counting([(0, 2), (1, 2), (2, 0)])) == -1  # the judge trusts nobody
    assert find_judge(1, counting([])) == 0
    assert find_judge(2, counting([])) == -1
    assert find_judge(2, counting([(0, 1)])) == 1
    assert find_judge(2, counting([(0, 1), (1, 0)])) == -1
    assert find_judge(4, counting([(0, 3), (1, 3), (2, 3), (0, 1), (2, 1)])) == 3


def test_judge_random():
    rng = random.Random(2)
    for _ in range(400):
        n = rng.randint(1, 8)
        pairs = [(a, b) for a in range(n) for b in range(n) if a != b]
        trust = rng.sample(pairs, rng.randint(0, len(pairs)))
        if n > 1 and rng.random() < 0.5:  # plant a judge, maybe spoil it
            j = rng.randrange(n)
            trust = [(a, b) for a, b in trust if a != j]
            trust += [(a, j) for a in range(n) if a != j and (a, j) not in trust]
            if rng.random() < 0.3:
                trust.append((j, (j + 1) % n))
            elif rng.random() < 0.3:
                trust.remove(rng.choice([p for p in trust if p[1] == j]))
            rng.shuffle(trust)
        assert find_judge(n, counting(trust)) == brute_judge(n, trust), (n, trust)


@pytest.mark.parametrize("spoil", [None, "judge trusts", "one missing"])
def test_judge_big_reads_each_pair_once(spoil):
    rng = random.Random(3)
    n, j = 200_000, 123_457
    trust = [(a, j) for a in range(n) if a != j]
    # 200,000 more pairs between the others, distinct by construction
    trust += [(a, (a + 1) % n) for a in range(n) if j not in (a, (a + 1) % n)]
    if spoil == "judge trusts":
        trust.append((j, 5))
    elif spoil == "one missing":
        trust.remove((77, j))
    rng.shuffle(trust)
    assert find_judge(n, counting(trust)) == (j if spoil is None else -1)


# 3. to_csr
def check_csr(adj, got):
    offsets, targets = (list(x) for x in got)
    n = len(adj)
    assert len(offsets) == n + 1 and offsets[0] == 0 and offsets[-1] == len(targets)
    for u in range(n):
        assert targets[offsets[u]:offsets[u + 1]] == adj[u], u


def test_csr_examples():
    assert tuple(map(list, to_csr([[1, 2], [2], []]))) == ([0, 2, 3, 3], [1, 2, 2])
    assert tuple(map(list, to_csr([]))) == ([0], [])
    assert tuple(map(list, to_csr([[], [], []]))) == ([0, 0, 0, 0], [])
    assert tuple(map(list, to_csr([[], [0, 0, 1]]))) == ([0, 0, 3], [0, 0, 1])


def test_csr_random_and_leaves_input_alone():
    rng = random.Random(4)
    for _ in range(300):
        adj = random_graph(rng, rng.randint(0, 12), 5)
        before = copy.deepcopy(adj)
        got = to_csr(adj)
        assert adj == before, "to_csr must not change adj"
        check_csr(adj, got)


def test_csr_big():
    n = 200_000
    adj = [[(u * 31 + i) % n for i in range(u % 11)] for u in range(n)]  # about 1,000,000 edges
    check_csr(adj, to_csr(adj))
