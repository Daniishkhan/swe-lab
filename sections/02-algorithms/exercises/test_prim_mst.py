import itertools
import random
import signal
import tracemalloc
from collections.abc import Sequence

import pytest

from prim_mst import prim_dense, prim_mst


@pytest.fixture(autouse=True)
def time_limit(request):
    """Heap Prim and array Prim each finish every test in a few seconds (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(
            "over the time cap: is every step rescanning all the cables of the tree, "
            "or scanning an array of all n towns (array Prim on a sparse graph), "
            "instead of popping the cheapest cable from a heap?"
        )

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm({"test_big_sparse_graph": 10, "test_dense_big": 20, "test_dense_memory": 20}.get(request.node.name, 5))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------- counting wrappers ----------

class TooManyReads(Exception):
    pass


class Tally:
    def __init__(self, budget):
        self.reads, self.budget = 0, budget

    def tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooManyReads(
                f"over {self.budget:,} adjacency reads: each (v, w) entry should be read about once, "
                "when its town joins the tree. Is every step rescanning the whole tree's cables?"
            )


class CountingRow(Sequence):
    """One town's neighbor list. Every entry read costs 1 from a shared budget."""

    def __init__(self, items, tally):
        self._items, self._tally = items, tally

    def __getitem__(self, i):
        if isinstance(i, slice):
            out = self._items[i]
            self._tally.tick(len(out))
            return CountingRow(out, self._tally)
        self._tally.tick()
        return self._items[i]

    def __iter__(self):
        for x in self._items:
            self._tally.tick()
            yield x

    def __len__(self):
        return len(self._items)


class CountingAdj(Sequence):
    def __init__(self, lists, budget):
        self.tally = Tally(budget)
        self._rows = [CountingRow(list(r), self.tally) for r in lists]

    def __getitem__(self, u):
        if isinstance(u, slice):
            return self._rows[u]
        return self._rows[u]

    def __len__(self):
        return len(self._rows)


def counting_adj(n, edges):
    lists = [[] for _ in range(n)]
    for u, v, w in edges:
        lists[u].append((v, w))
        lists[v].append((u, w))
    entries = sum(len(r) for r in lists)
    return CountingAdj(lists, 2 * entries + 2 * n + 50)


# ---------- helpers (no MST algorithm in here) ----------

def connects_all(n, chosen):
    label = list(range(n))
    for u, v, *_ in chosen:
        a, b = label[u], label[v]
        if a != b:
            label = [a if x == b else x for x in label]
    return len(set(label)) == 1


def brute_cost(n, edges):
    """Try every set of n - 1 cables. Exponential: small inputs only."""
    best = None
    for combo in itertools.combinations(edges, n - 1):
        if connects_all(n, combo):
            cost = sum(w for _, _, w in combo)
            best = cost if best is None else min(best, cost)
    return best


def check_parent(n, parent, cheapest):
    """parent must describe a tree rooted at 0 using real cables. Returns the tree's cost."""
    assert isinstance(parent, list) and len(parent) == n, "parent must be a list with one entry per town"
    assert parent[0] == -1, "parent[0] must be -1 (town 0 is the root)"
    reaches_root = [False] * n
    reaches_root[0] = True
    for v in range(1, n):
        path, x = [], v
        while not reaches_root[x]:
            path.append(x)
            x = parent[x]
            assert 0 <= x < n, f"parent pointer {x} is not a town"
            assert len(path) <= n, "the parent pointers loop instead of reaching town 0"
        for y in path:
            reaches_root[y] = True
    total = 0
    for v in range(1, n):
        key = (min(v, parent[v]), max(v, parent[v]))
        assert key in cheapest, f"there is no cable between {parent[v]} and {v}"
        total += cheapest[key]
    return total


def cheapest_cables(edges):
    best = {}
    for u, v, w in edges:
        key = (min(u, v), max(u, v))
        if key not in best or w < best[key]:
            best[key] = w
    return best


def planted(n, rng, extra_near, extra_far):
    """A graph whose unique MST is a tree we build first (see test_kruskal_mst.py for the idea):
    every extra cable is strictly the most expensive cable on the loop it closes."""
    parent, cost = [-1] * n, [0] * n
    tree = []
    for i in range(1, n):
        parent[i] = rng.randrange(max(0, i - 1000), i)
        cost[i] = rng.randint(1, 1_000_000)
        tree.append((parent[i], i, cost[i]))
    extras = []
    for _ in range(extra_near):
        i = rng.randrange(1, n)
        if parent[i] > 0 and rng.random() < 0.7:
            extras.append((i, parent[parent[i]], max(cost[i], cost[parent[i]]) + rng.randint(1, 1000)))
        else:
            extras.append((parent[i], i, cost[i] + rng.randint(1, 1000)))
    for _ in range(extra_far):
        extras.append((rng.randrange(n), rng.randrange(n), rng.randint(1_002_000, 3_000_000)))
    for _ in range(20):
        u = rng.randrange(n)
        extras.append((u, u, -5))
    edges = tree + extras
    rng.shuffle(edges)
    return edges, parent, sum(cost)


class CountingDist:
    """dist(i, j) for points on a grid (Manhattan distance), with a call budget."""

    def __init__(self, pts, budget):
        self.xs = [p[0] for p in pts]
        self.ys = [p[1] for p in pts]
        self.calls, self.budget = 0, budget

    def __call__(self, i, j):
        self.calls += 1
        if self.calls > self.budget:
            raise TooManyReads(f"over {self.budget:,} calls to dist(): array Prim needs about n^2 / 2")
        return abs(self.xs[i] - self.xs[j]) + abs(self.ys[i] - self.ys[j])


def points(n, seed):
    rng = random.Random(seed)
    return [(rng.randrange(1_000_000), rng.randrange(1_000_000)) for _ in range(n)]


# ---------- prim_mst ----------

def test_example():
    adj = [[(1, 4), (2, 1)], [(0, 4), (2, 2)], [(0, 1), (1, 2)]]
    assert prim_mst(3, adj) == (3, [-1, 2, 0])


def test_one_town():
    assert prim_mst(1, [[]]) == (0, [-1])
    assert prim_mst(1, [[(0, 5), (0, 5)]]) == (0, [-1])


def test_disconnected_raises():
    with pytest.raises(ValueError):
        prim_mst(2, [[], []])
    with pytest.raises(ValueError):
        prim_mst(4, counting_adj(4, [(0, 1, 1), (2, 3, 1)]))


def test_parallel_cables_self_loops_negative_costs():
    edges = [(0, 1, 9), (1, 0, 4), (1, 1, -50), (1, 2, -6), (2, 2, 0), (0, 2, 7)]
    total, parent = prim_mst(3, counting_adj(3, edges))
    assert total == -2
    assert check_parent(3, parent, cheapest_cables(edges)) == -2


def test_random_small_graphs_against_brute_force():
    rng = random.Random(2009)
    for _ in range(300):
        n = rng.randint(2, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 9)) for _ in range(rng.randint(0, 10))]
        want = brute_cost(n, edges)
        adj = counting_adj(n, edges)
        if want is None:
            with pytest.raises(ValueError):
                prim_mst(n, adj)
            continue
        total, parent = prim_mst(n, adj)
        assert total == want, (n, edges)
        assert check_parent(n, parent, cheapest_cables(edges)) == want


def test_reads_each_entry_about_once():
    """A path 0-1-2-...-n with many extra cables back to town 0. Rescanning the tree's
    cables at each step reads the hub's long list again and again."""
    n = 400
    edges = [(i, i + 1, 1) for i in range(n - 1)] + [(0, i, 1000 + i) for i in range(2, n)]
    adj = counting_adj(n, edges)
    total, parent = prim_mst(n, adj)
    assert total == n - 1
    assert parent == [-1] + list(range(n - 1))


def test_planted_medium():
    rng = random.Random(7)
    edges, want_parent, want_total = planted(500, rng, 800, 800)
    total, parent = prim_mst(500, counting_adj(500, edges))
    assert total == want_total
    assert parent == want_parent, "the planted tree is the only MST here"


def test_big_sparse_graph():
    """60,000 towns, about 200,000 cables, under a read budget and a 10-second cap.
    Heap Prim: about a second. Copying the lists and rescanning the tree's cables, or
    array Prim's V^2 = 3.6 billion scan steps, is minutes."""
    rng = random.Random(42)
    n = 60_000
    edges, want_parent, want_total = planted(n, rng, 80_000, 60_000)
    total, parent = prim_mst(n, counting_adj(n, edges))
    assert total == want_total
    assert parent == want_parent


# ---------- prim_dense ----------

def test_dense_tiny():
    assert prim_dense(1, CountingDist([(5, 5)], 1)) == (0, [-1])
    total, parent = prim_dense(2, CountingDist([(0, 0), (3, 4)], 4))
    assert (total, parent) == (7, [-1, 0])


def test_dense_against_brute_force():
    for seed in range(60):
        n = 2 + seed % 5
        pts = [(x % 50, y % 50) for x, y in points(n, seed)]
        d = CountingDist(pts, n * n)
        edges = [(i, j, d(i, j)) for i in range(n) for j in range(i + 1, n)]
        want = brute_cost(n, edges)
        d.calls = 0
        total, parent = prim_dense(n, d)
        assert total == want, pts
        assert check_parent(n, parent, cheapest_cables(edges)) == want


def test_dense_big():
    """1,500 points: about 1.1 million pairs. Array Prim calls dist() about n^2 / 2 times.
    The expected total was computed offline."""
    n = 1500
    d = CountingDist(points(n, 1500), n * n)
    total, parent = prim_dense(n, d)
    assert total == DENSE_BIG_TOTAL
    assert check_parent_dense(n, parent, d) == total


def test_dense_memory():
    """O(n) extra memory: no edge list, no heap of n^2 / 2 entries, no distance matrix."""
    n = 600
    d = CountingDist(points(n, 600), 10 * n * n)
    tracemalloc.start()
    try:
        total, parent = prim_dense(n, d)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert total == DENSE_MEMORY_TOTAL
    assert peak < 150_000 + 250 * n, (
        f"peak extra memory {peak:,} bytes for n = {n}: are you storing the n^2 / 2 cables "
        "(an edge list, a heap of pairs, or a distance matrix)? Keep one best[] array."
    )


def check_parent_dense(n, parent, d):
    d.budget = float("inf")
    assert parent[0] == -1 and len(parent) == n
    seen = [False] * n
    seen[0] = True
    for v in range(1, n):
        path, x = [], v
        while not seen[x]:
            path.append(x)
            x = parent[x]
            assert 0 <= x < n, f"parent pointer {x} is not a point"
            assert len(path) <= n, "the parent pointers loop"
        for y in path:
            seen[y] = True
    return sum(d(parent[v], v) for v in range(1, n))


# Computed offline (seeded points above, Manhattan distance).
DENSE_BIG_TOTAL = 31_890_622
DENSE_MEMORY_TOTAL = 19_825_922
