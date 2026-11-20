import itertools
import math
import random
import signal
from collections import deque

import pytest

from mst_clustering import k_clusters, widest_path


@pytest.fixture(autouse=True)
def time_limit(request):
    """Sort + union-find finishes each test in a few seconds (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(
            "over the time cap: is there a BFS/DFS per cable (or per bandwidth), "
            "instead of one sort and a union-find?"
        )

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm({"test_big_clusters": 20, "test_big_widest": 20}.get(request.node.name, 5))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------- helpers (brute force only, small inputs) ----------

def spacing_of(edges, labels):
    gaps = [d for u, v, d in edges if labels[u] != labels[v]]
    return min(gaps) if gaps else math.inf


def brute_best_spacing(n, edges, k):
    best = -math.inf
    for labels in itertools.product(range(k), repeat=n):
        if len(set(labels)) == k:
            best = max(best, spacing_of(edges, labels))
    return best


def connected_graph(rng, n, extra, lo, hi):
    edges = [(rng.randrange(i), i, rng.randint(lo, hi)) for i in range(1, n)]
    for _ in range(extra):
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges.append((u, v, rng.randint(lo, hi)))
    rng.shuffle(edges)
    return edges


def reaches(n, edges, s, t, at_least):
    adj = [[] for _ in range(n)]
    for u, v, c in edges:
        if c >= at_least:
            adj[u].append(v)
            adj[v].append(u)
    seen, q = {s}, deque([s])
    while q:
        x = q.popleft()
        if x == t:
            return True
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                q.append(y)
    return False


def brute_widest(n, edges, s, t):
    if s == t:
        return math.inf
    for c in sorted({c for *_, c in edges}, reverse=True):
        if reaches(n, edges, s, t, c):
            return c
    return 0


def same_partition(a, b):
    """True if label lists a and b group the items the same way."""
    fwd, back = {}, {}
    for x, y in zip(a, b):
        if fwd.setdefault(x, y) != y or back.setdefault(y, x) != x:
            return False
    return True


# ---------- k_clusters ----------

def test_clusters_example():
    spacing, labels = k_clusters(4, [(0, 1, 1), (2, 3, 2), (1, 2, 10), (0, 3, 12)], 2)
    assert spacing == 10
    assert same_partition(labels, [0, 0, 1, 1])


def test_one_cluster():
    edges = [(0, 1, 4), (1, 2, 1)]
    spacing, labels = k_clusters(3, edges, 1)
    assert spacing == math.inf
    assert len(set(labels)) == 1 and len(labels) == 3


def test_every_point_alone():
    edges = [(0, 1, 4), (1, 2, 9), (0, 2, 6)]
    spacing, labels = k_clusters(3, edges, 3)
    assert spacing == 4
    assert len(set(labels)) == 3


def test_ties_and_parallel_links():
    edges = [(0, 1, 2), (1, 2, 2), (2, 3, 2), (0, 1, 1), (3, 0, 5)]
    spacing, labels = k_clusters(4, edges, 2)
    assert spacing == 2
    assert len(set(labels)) == 2
    assert spacing_of(edges, labels) == 2


def test_clusters_against_brute_force():
    rng = random.Random(9)
    for _ in range(150):
        n = rng.randint(2, 6)
        k = rng.randint(1, min(n, 4))
        edges = connected_graph(rng, n, rng.randint(0, 6), 1, 12)
        spacing, labels = k_clusters(n, edges, k)
        assert len(labels) == n
        assert len(set(labels)) == k, f"asked for {k} groups, got {len(set(labels))}"
        assert spacing_of(edges, labels) == spacing, "the returned spacing doesn't match the returned groups"
        assert spacing == brute_best_spacing(n, edges, k), (n, k, edges)


def test_big_clusters():
    """100,000 points in 40 planted clusters. Inside a cluster every listed distance is
    below S; between clusters every listed distance is at least S, and one is exactly S."""
    rng = random.Random(40)
    n, k, S = 100_000, 40, 1_000_000
    group = [i % k for i in range(n)]
    members = [[] for _ in range(k)]
    for i in range(n):
        members[group[i]].append(i)
    edges = []
    for m in members:  # a random tree plus extras inside each cluster, all below S
        for j in range(1, len(m)):
            edges.append((m[rng.randrange(j)], m[j], rng.randint(1, S - 1)))
        for _ in range(len(m)):
            edges.append((rng.choice(m), rng.choice(m), rng.randint(1, S - 1)))
    for g in range(1, k):  # a chain so the whole graph is connected, then random cross links
        edges.append((rng.choice(members[g - 1]), rng.choice(members[g]), rng.randint(S + 1, 5 * S)))
    for _ in range(50_000):
        u, v = rng.randrange(n), rng.randrange(n)
        if group[u] != group[v]:
            edges.append((u, v, rng.randint(S + 1, 5 * S)))
    edges.append((members[3][0], members[17][0], S))
    edges = [e for e in edges if e[0] != e[1]]
    rng.shuffle(edges)
    spacing, labels = k_clusters(n, edges, k)
    assert spacing == S
    assert same_partition(labels, group)


# ---------- widest_path ----------

def test_widest_example():
    assert widest_path(4, [(0, 1, 5), (1, 3, 2), (0, 2, 3), (2, 3, 4)], 0, 3) == 3


def test_widest_same_node_and_unreachable():
    assert widest_path(3, [(0, 1, 5)], 2, 2) == math.inf
    assert widest_path(3, [(0, 1, 5)], 0, 2) == 0
    assert widest_path(1, [], 0, 0) == math.inf


def test_widest_parallel_links():
    assert widest_path(2, [(0, 1, 1), (1, 0, 8), (0, 1, 3)], 0, 1) == 8


def test_widest_against_brute_force():
    rng = random.Random(11)
    for _ in range(300):
        n = rng.randint(1, 8)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 15)) for _ in range(rng.randint(0, 12))]
        s, t = rng.randrange(n), rng.randrange(n)
        assert widest_path(n, edges, s, t) == brute_widest(n, edges, s, t), (n, edges, s, t)


def test_big_widest():
    """Two halves joined only by narrow links, one of width exactly C. Inside each half
    the links are wide and almost all widths are different, so scanning widths from the
    top with one BFS each does about 180,000 BFS runs (one per distinct width above C)."""
    rng = random.Random(77)
    n, C = 100_000, 500_000
    half = n // 2
    edges = []
    for lo, hi in ((0, half), (half, n)):
        for i in range(lo + 1, hi):
            edges.append((rng.randrange(lo, i), i, rng.randint(C + 1, 100 * C)))
        for _ in range(40_000):
            edges.append((rng.randrange(lo, hi), rng.randrange(lo, hi), rng.randint(C + 1, 100 * C)))
    for _ in range(20_000):
        edges.append((rng.randrange(half), rng.randrange(half, n), rng.randint(1, C - 1)))
    edges.append((rng.randrange(half), rng.randrange(half, n), C))
    rng.shuffle(edges)
    assert widest_path(n, edges, 0, n - 1) == C
