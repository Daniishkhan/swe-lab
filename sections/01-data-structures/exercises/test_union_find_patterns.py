import itertools
import random
import signal
from collections import Counter

import pytest

from union_find_patterns import islands_after_each, link_accounts, min_spanning_tree


@pytest.fixture(autouse=True)
def time_limit():
    """Union-find answers each big test in about half a second; the slow ways
    take minutes (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something comparing every pair, or rescanning everything after each step?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------- helpers (slow on purpose) ----------

def components(n, pairs):
    """Label every node with the smallest node it can reach, by repeated passes."""
    label = list(range(n))
    changed = True
    while changed:
        changed = False
        for a, b in pairs:
            m = min(label[a], label[b])
            if label[a] != m or label[b] != m:
                label[a] = label[b] = m
                changed = True
    return label


def groups_from_labels(label):
    out = {}
    for i, l in enumerate(label):
        out.setdefault(l, []).append(i)
    return sorted(out.values(), key=lambda g: g[0])


def count_islands(rows, cols, land):
    seen, k = set(), 0
    for cell in land:
        if cell in seen:
            continue
        k += 1
        seen.add(cell)
        todo = [cell]
        while todo:
            r, c = todo.pop()
            for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nb in land and nb not in seen:
                    seen.add(nb)
                    todo.append(nb)
    return k


def check_spanning_tree(n, edges, got):
    """got is a valid spanning tree made of input edges; returns its total."""
    total, chosen = got
    assert len(chosen) == n - 1, f"a spanning tree of {n} places has {n - 1} edges, got {len(chosen)}"
    have = Counter(edges)
    for e in chosen:
        assert have[e] > 0, f"{e} is not one of the input edges (or was used twice)"
        have[e] -= 1
    assert total == sum(w for _, _, w in chosen), "total doesn't match the chosen edges"
    label = components(n, [(u, v) for u, v, _ in chosen])
    assert len(set(label)) == 1, "the chosen edges don't connect every place"
    return total


# ---------- 1. link_accounts ----------

def test_link_accounts_example():
    assert link_accounts([["a", "b"], ["c"], ["b", "d"], [], ["d", "e"], ["c"]]) == [[0, 2, 4], [1, 5], [3]]
    assert link_accounts([]) == []
    assert link_accounts([[]]) == [[0]]
    assert link_accounts([["x", "x"], ["x"]]) == [[0, 1]]


def test_link_accounts_needs_chains():
    # 0 and 3 share nothing directly, but 0-1 share "p", 1-2 share "q", 2-3 share "r".
    accts = [["p", "m0"], ["q", "p"], ["r", "q"], ["r"], ["solo"]]
    assert link_accounts(accts) == [[0, 1, 2, 3], [4]]


def test_link_accounts_random():
    rng = random.Random(1)
    for _ in range(300):
        n = rng.randint(0, 15)
        accts = [[f"id{rng.randint(0, 20)}" for _ in range(rng.randint(0, 3))] for _ in range(n)]
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if set(accts[i]) & set(accts[j])]
        assert link_accounts(accts) == groups_from_labels(components(n, pairs)), accts


def test_link_accounts_many():
    n, n_groups = 100_000, 20_000
    rng = random.Random(3)
    group_of = [rng.randrange(n_groups) for _ in range(n)]
    members = {}
    for i, g in enumerate(group_of):
        members.setdefault(g, []).append(i)
    accts = [[f"own-{i}"] for i in range(n)]
    for g, idx in members.items():
        rng.shuffle(idx)
        for k in range(len(idx) - 1):  # a chain: each account shares one id with the next
            shared = f"g{g}-{k}"
            accts[idx[k]].append(shared)
            accts[idx[k + 1]].append(shared)
    expected = sorted((sorted(v) for v in members.values()), key=lambda m: m[0])
    assert link_accounts(accts) == expected


# ---------- 2. islands_after_each ----------

def test_islands_example():
    assert islands_after_each(3, 3, [(0, 0), (0, 1), (1, 2), (2, 1), (1, 1)]) == [1, 1, 2, 3, 1]
    assert islands_after_each(2, 2, []) == []
    assert islands_after_each(1, 1, [(0, 0), (0, 0)]) == [1, 1]


def test_islands_corners_dont_touch():
    assert islands_after_each(2, 2, [(0, 0), (1, 1), (0, 1)]) == [1, 2, 1]
    assert islands_after_each(1, 5, [(0, 0), (0, 4), (0, 2), (0, 1), (0, 3)]) == [1, 2, 3, 2, 1]


def test_islands_random():
    rng = random.Random(4)
    for _ in range(150):
        rows, cols = rng.randint(1, 6), rng.randint(1, 6)
        cells = [(rng.randrange(rows), rng.randrange(cols)) for _ in range(rng.randint(0, 25))]
        land, want = set(), []
        for cell in cells:
            land.add(cell)
            want.append(count_islands(rows, cols, land))
        assert islands_after_each(rows, cols, cells) == want, (rows, cols, cells)


def test_islands_big_grid():
    rows = cols = 300
    rng = random.Random(5)
    cells = [(rng.randrange(rows), rng.randrange(cols)) for _ in range(60_000)]
    got = islands_after_each(rows, cols, cells)
    assert len(got) == len(cells)
    for step in (0, 999, 19_999, 39_999, 59_999):
        want = count_islands(rows, cols, set(cells[: step + 1]))
        assert got[step] == want, f"after step {step + 1}: {got[step]} islands, expected {want}"


# ---------- 3. min_spanning_tree ----------

def test_mst_example():
    edges = [(0, 1, 1), (1, 2, 2), (0, 2, 3), (2, 3, 4), (1, 3, 5)]
    got = min_spanning_tree(4, edges)
    assert got is not None and got[0] == 7
    assert sorted(got[1]) == [(0, 1, 1), (1, 2, 2), (2, 3, 4)]


def test_mst_edge_cases():
    assert min_spanning_tree(0, []) == (0, [])
    assert min_spanning_tree(1, []) == (0, [])
    assert min_spanning_tree(1, [(0, 0, 5)]) == (0, [])
    assert min_spanning_tree(3, [(0, 1, 1)]) is None  # 2 can't be reached
    assert min_spanning_tree(2, []) is None
    got = min_spanning_tree(2, [(0, 1, 9), (1, 0, 4), (0, 0, 1)])  # parallel edges and a self-loop
    assert got == (4, [(1, 0, 4)])


def test_mst_small_random_is_optimal():
    rng = random.Random(6)
    for _ in range(120):
        n = rng.randint(2, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 9)) for _ in range(rng.randint(0, 9))]
        best = None
        for subset in itertools.combinations(edges, n - 1):  # try every set of n - 1 edges
            if len(set(components(n, [(u, v) for u, v, _ in subset]))) == 1:
                cost = sum(w for _, _, w in subset)
                best = cost if best is None else min(best, cost)
        got = min_spanning_tree(n, edges)
        if best is None:
            assert got is None, (n, edges)
        else:
            assert got is not None, (n, edges)
            assert check_spanning_tree(n, edges, got) == best, (n, edges)


def test_mst_medium_passes_the_cycle_check():
    # Every edge left out must be at least as costly as each edge on the tree
    # path it would close into a cycle. If not, swapping them would be cheaper.
    rng = random.Random(7)
    n = 120
    edges = [(i, rng.randrange(i), rng.randint(1, 50)) for i in range(1, n)]
    edges += [(rng.randrange(n), rng.randrange(n), rng.randint(1, 50)) for _ in range(600)]
    got = min_spanning_tree(n, edges)
    assert got is not None
    check_spanning_tree(n, edges, got)
    adj = {i: [] for i in range(n)}
    for u, v, w in got[1]:
        adj[u].append((v, w))
        adj[v].append((u, w))

    def heaviest_on_path(a, b):
        stack, seen = [(a, 0)], {a}
        while stack:
            x, heavy = stack.pop()
            if x == b:
                return heavy
            for y, w in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append((y, max(heavy, w)))

    for u, v, w in edges:
        if u != v:
            assert heaviest_on_path(u, v) <= w, f"edge {(u, v, w)} is cheaper than an edge on the tree path between {u} and {v}"


def test_mst_big():
    # A planted tree: place i hangs off an earlier place, and that cable costs i.
    # Each extra cable (u, v) costs more than max(u, v), the dearest cable on
    # the tree path between u and v, so the planted tree is the only answer.
    # The extras are mixed in with the tree cables by cost, so most of them
    # arrive when u and v are already in one big group.
    n = 100_000
    rng = random.Random(8)
    tree = [(i, rng.randrange(i), i) for i in range(1, n)]
    extra = []
    for _ in range(200_000):
        u, v = rng.randrange(n), rng.randrange(n)
        extra.append((u, v, max(u, v) + rng.randint(1, 1000)))
    edges = tree + extra
    rng.shuffle(edges)
    got = min_spanning_tree(n, edges)
    assert got is not None and got[0] == sum(w for _, _, w in tree)
    assert sorted(got[1]) == sorted(tree)
