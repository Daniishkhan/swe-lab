import itertools
import random
import signal
from collections import Counter

import pytest

from kruskal_mst import kruskal_mst


@pytest.fixture(autouse=True)
def time_limit(request):
    """Sort + union-find finishes the big test in a few seconds (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(
            "over the time cap: is each cable checked by searching the tree for a path (BFS/DFS), "
            "or is find() walking long chains (no union by size / path compression)?"
        )

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm({"test_big_sparse_graph": 20}.get(request.node.name, 5))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------- helpers (no MST algorithm in here) ----------

def connects_all(n, chosen):
    """True if the chosen cables join all n towns (plain label merging, O(n * E))."""
    label = list(range(n))
    for u, v, _ in chosen:
        a, b = label[u], label[v]
        if a != b:
            label = [a if x == b else x for x in label]
    return len(set(label)) == 1


def check_tree(n, edges, chosen):
    assert isinstance(chosen, list), "return a list of cables"
    assert len(chosen) == n - 1, f"a spanning tree on {n} towns has {n - 1} cables, got {len(chosen)}"
    have = Counter(edges)
    for e in chosen:
        assert have[e] > 0, f"{e} is not one of the input cables (or is used twice); return the input tuples as given"
        have[e] -= 1
    assert connects_all(n, chosen), "the chosen cables leave some town unconnected (so they contain a loop)"


def brute_cost(n, edges):
    """Try every set of n - 1 cables. Exponential: small inputs only."""
    best = None
    for combo in itertools.combinations(edges, n - 1):
        if connects_all(n, combo):
            cost = sum(w for _, _, w in combo)
            best = cost if best is None else min(best, cost)
    return best


def planted(n, rng, extra_near, extra_far):
    """A graph whose unique MST is a tree we build first.

    Town i > 0 hangs off parent p(i) < i with cost w(i). Extra cables are then
    added so that each one is strictly the most expensive cable on the loop it
    closes (the cycle property), so none of them can be in any MST:
      - "near" cables go to the parent or grandparent, a little more expensive
        than the tree cables on that short path, so they interleave with the
        tree cables in sorted order;
      - "far" cables join random towns and cost more than every tree cable;
      - a few self-loops cost less than everything.
    """
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
            g = parent[parent[i]]
            extras.append((i, g, max(cost[i], cost[parent[i]]) + rng.randint(1, 1000)))
        else:
            extras.append((parent[i], i, cost[i] + rng.randint(1, 1000)))  # a parallel cable
    for _ in range(extra_far):
        extras.append((rng.randrange(n), rng.randrange(n), rng.randint(1_002_000, 3_000_000)))
    for _ in range(20):
        u = rng.randrange(n)
        extras.append((u, u, -5))
    edges = tree + extras
    rng.shuffle(edges)
    return edges, tree


# ---------- tests ----------

def test_example():
    edges = [(0, 1, 1), (1, 2, 2), (0, 2, 3), (2, 3, 4)]
    got = kruskal_mst(4, edges)
    check_tree(4, edges, got)
    assert sorted(got) == [(0, 1, 1), (1, 2, 2), (2, 3, 4)]


def test_one_town():
    assert kruskal_mst(1, []) == []
    assert kruskal_mst(1, [(0, 0, 3)]) == []


def test_disconnected_raises():
    with pytest.raises(ValueError):
        kruskal_mst(2, [])
    with pytest.raises(ValueError):
        kruskal_mst(4, [(0, 1, 1), (2, 3, 1), (0, 1, 5)])


def test_cheapest_n_minus_1_is_wrong():
    # The three cheapest cables form a triangle; town 3 is only reachable by the expensive one.
    edges = [(0, 1, 1), (1, 2, 1), (0, 2, 1), (2, 3, 100)]
    got = kruskal_mst(4, edges)
    check_tree(4, edges, got)
    assert sum(w for *_, w in got) == 102


def test_parallel_cables_and_self_loops():
    edges = [(0, 1, 9), (1, 0, 4), (1, 1, -50), (1, 2, 6), (2, 2, 0), (0, 2, 7)]
    got = kruskal_mst(3, edges)
    check_tree(3, edges, got)
    assert sorted(got) == [(1, 0, 4), (1, 2, 6)]


def test_negative_and_zero_costs():
    edges = [(0, 1, -3), (1, 2, 0), (2, 3, -1), (0, 3, -2), (1, 3, 5)]
    got = kruskal_mst(4, edges)
    check_tree(4, edges, got)
    assert sum(w for *_, w in got) == -6


def test_all_costs_equal():
    rng = random.Random(3)
    n = 30
    edges = [(rng.randrange(i), i, 7) for i in range(1, n)] + [(rng.randrange(n), rng.randrange(n), 7) for _ in range(60)]
    got = kruskal_mst(n, edges)
    check_tree(n, edges, got)
    assert sum(w for *_, w in got) == 7 * (n - 1)


def test_input_list_unchanged():
    edges = [(2, 3, 4), (0, 1, 1), (0, 2, 3), (1, 2, 2)]
    before = list(edges)
    kruskal_mst(4, edges)
    assert edges == before, "kruskal_mst sorted or changed the caller's list; sort a copy instead"


def test_random_small_graphs_against_brute_force():
    rng = random.Random(2009)
    for _ in range(300):
        n = rng.randint(2, 6)
        edges = [(rng.randrange(n), rng.randrange(n), rng.randint(-3, 9)) for _ in range(rng.randint(0, 10))]
        want = brute_cost(n, edges)
        if want is None:
            with pytest.raises(ValueError):
                kruskal_mst(n, edges)
            continue
        got = kruskal_mst(n, edges)
        check_tree(n, edges, got)
        assert sum(w for *_, w in got) == want, (n, edges)


def test_star_in_both_orientations():
    """Every cable touches town 0, cheapest first. Without union by size or path
    compression, one of these two orders turns the union-find into a chain of
    50,000 that find(0) walks again for every cable."""
    n = 50_000
    for edges in ([(0, i, i) for i in range(1, n)], [(i, 0, i) for i in range(1, n)]):
        got = kruskal_mst(n, edges)
        assert len(got) == n - 1
        assert sum(w for *_, w in got) == n * (n - 1) // 2


def test_planted_medium():
    rng = random.Random(7)
    edges, tree = planted(500, rng, extra_near=800, extra_far=800)
    got = kruskal_mst(500, edges)
    assert sorted(got) == sorted(tree), "the planted tree is the only MST here"


def test_big_sparse_graph():
    """100,000 towns and about 300,000 cables. Sort + union-find: a few seconds.
    A path search per cable is around 10^10 steps."""
    rng = random.Random(42)
    n = 100_000
    edges, tree = planted(n, rng, extra_near=120_000, extra_far=80_000)
    got = kruskal_mst(n, edges)
    assert len(got) == n - 1
    assert sorted(got) == sorted(tree), "the planted tree is the only MST here"
