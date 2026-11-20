import math
import random
import signal

import pytest

from union_find import UnionFind


@pytest.fixture(autouse=True)
def time_limit(request):
    """Every test finishes in a few seconds at most with both tricks (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: are the trees getting tall, or is find walking the same long path again and again?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm({"test_a_million_operations": 20}.get(request.node.name, 10))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class CountingList(list):
    """A list that counts every read of an item (class-wide)."""

    reads = 0

    def __getitem__(self, i):
        CountingList.reads += 1
        return list.__getitem__(self, i)


def heights(parent):
    """How many steps each item is from its root, read straight from the list."""
    parent = list(parent)
    out = []
    for x in range(len(parent)):
        d = 0
        while parent[x] != x:
            x = parent[x]
            d += 1
            assert d <= len(parent), "the parent pointers loop: a root must point at itself"
        out.append(d)
    return out


def brute_groups(n, pairs):
    label = list(range(n))
    for a, b in pairs:
        la, lb = label[a], label[b]
        if la != lb:
            label = [la if l == lb else l for l in label]
    return label


def test_example():
    uf = UnionFind(6)
    assert uf.union(0, 1) is True
    assert uf.union(1, 2) is True
    assert uf.union(0, 2) is False
    assert uf.connected(0, 2) is True
    assert uf.connected(0, 3) is False
    assert uf.components == 4
    assert uf.group_size(1) == 3 and uf.group_size(4) == 1


def test_starts_disjoint():
    uf = UnionFind(5)
    assert uf.components == 5
    assert uf.parent == [0, 1, 2, 3, 4]
    assert all(uf.find(x) == x for x in range(5))
    assert all(uf.group_size(x) == 1 for x in range(5))
    assert not uf.connected(0, 1)
    assert uf.connected(3, 3)


def test_smallest_and_empty():
    one = UnionFind(1)
    assert one.components == 1 and one.find(0) == 0
    assert one.union(0, 0) is False and one.components == 1
    assert UnionFind(0).components == 0


def test_find_returns_a_root():
    uf = UnionFind(10)
    for a, b in [(0, 1), (2, 3), (1, 3), (5, 6), (6, 7), (7, 5), (9, 0)]:
        uf.union(a, b)
    for x in range(10):
        r = uf.find(x)
        assert uf.parent[r] == r, f"find({x}) returned {r}, but parent[{r}] is {uf.parent[r]}: a root points at itself"
    assert uf.find(0) == uf.find(2) == uf.find(9)
    assert uf.find(5) == uf.find(7) != uf.find(0)
    assert uf.components == 4  # {0,1,2,3,9} {4} {5,6,7} {8}
    assert uf.group_size(9) == 5 and uf.group_size(6) == 3


def test_random_against_brute_force():
    rng = random.Random(1)
    for _ in range(200):
        n = rng.randint(1, 30)
        uf = UnionFind(n)
        pairs = []
        for _ in range(rng.randint(0, 40)):
            a, b = rng.randrange(n), rng.randrange(n)
            label = brute_groups(n, pairs)
            assert uf.union(a, b) is (label[a] != label[b])
            pairs.append((a, b))
            label = brute_groups(n, pairs)
            assert uf.components == len(set(label))
            x, y = rng.randrange(n), rng.randrange(n)
            assert uf.connected(x, y) is (label[x] == label[y])
            assert uf.group_size(x) == label.count(label[x])


@pytest.mark.parametrize("order", ["i, i+1", "i+1, i", "pairs", "random"])
def test_trees_stay_short(order):
    n = 2 ** 14
    uf = UnionFind(n)
    if order == "i, i+1":
        for i in range(n - 1):
            uf.union(i, i + 1)
    elif order == "i+1, i":
        for i in range(n - 1):
            uf.union(i + 1, i)
    elif order == "pairs":  # merge equal-sized groups: the worst case for union by size
        k = 1
        while k < n:
            for i in range(0, n, 2 * k):
                uf.union(i, i + k)
            k *= 2
    else:
        rng = random.Random(5)
        for _ in range(2 * n):
            uf.union(rng.randrange(n), rng.randrange(n))
    tallest = max(heights(uf.parent))
    limit = int(math.log2(n))
    assert tallest <= limit, f"an item is {tallest} steps from its root after unions in order ({order}); union by size keeps it within log2(n) = {limit}"
    if order != "random":
        assert uf.components == 1 and uf.group_size(123) == n


def test_find_compresses_paths():
    length, chains = 400, 100
    n = length * chains
    uf = UnionFind(n)
    p = list(range(n))
    for c in range(chains):  # chain c: c*400 -> c*400+1 -> ... -> c*400+399 (the root)
        for j in range(length - 1):
            p[c * length + j] = c * length + j + 1
    uf.parent = CountingList(p)
    order = list(range(n))
    random.Random(2).shuffle(order)
    CountingList.reads = 0
    for x in order:
        root = (x // length) * length + length - 1
        assert uf.find(x) == root
    per = CountingList.reads / n
    assert per <= 40, f"{per:.0f} reads of self.parent per find on 400-long chains (budget 40): is find pointing the path it walked at the root?"


def test_compression_flattens_the_path():
    uf = UnionFind(8)
    uf.parent = [1, 2, 3, 4, 5, 6, 7, 7]  # one chain, 0 -> 1 -> ... -> 7
    assert uf.find(0) == 7
    before = 7
    after = heights(uf.parent)[0]
    assert after < before, "find(0) walked 7 steps but left 0 just as far from the root"
    assert uf.find(0) == 7


def test_a_million_operations():
    n = 1_000_000
    uf = UnionFind(n)
    rng = random.Random(9)
    merged = 0
    for _ in range(n):
        if uf.union(rng.randrange(n), rng.randrange(n)):
            merged += 1
    assert uf.components == n - merged
    hits = sum(uf.connected(rng.randrange(n), rng.randrange(n)) for _ in range(n))
    assert 0 < hits < n
