import math
import random
import signal

import pytest

from bellman_ford import bellman_ford, negative_cycle


class TooMuchWork(AssertionError):
    pass


# ---------------------------------------------------------------------------
# Counting weights: every edge weight is a W, a float that counts each time
# it is added to something. One round over all E edges costs E additions
# (2E if you compute dist[u] + w twice). Past the budget, the next addition
# raises, so slow code fails fast.
# ---------------------------------------------------------------------------
class W(float):
    adds = 0
    limit = None

    @staticmethod
    def _tick():
        W.adds += 1
        if W.limit is not None and W.adds > W.limit:
            raise TooMuchWork(f"over {W.limit:,} additions of an edge weight: too many rounds over the edges")

    def __add__(self, other):
        W._tick()
        return float.__add__(self, other)

    def __radd__(self, other):
        W._tick()
        return float.__radd__(self, other)


class rounds_at_most:
    """Allow `rounds` full passes over `edges`, at 2 additions per edge."""

    def __init__(self, rounds, edges):
        self.limit = 2 * rounds * max(1, len(edges)) + 2

    def __enter__(self):
        W.adds, W.limit = 0, self.limit
        return self

    def __exit__(self, *exc):
        W.limit = None
        return False


def wrap(edges):
    return [(u, v, W(w)) for u, v, w in edges]


@pytest.fixture(autouse=True)
def time_limit():
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 20 s time cap")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        W.limit = None


# ---------------------------------------------------------------------------
# Brute force for small graphs: list every simple cycle and every simple path.
# ---------------------------------------------------------------------------
def cheapest_pairs(edges):
    best = {}
    for u, v, w in edges:
        if (u, v) not in best or w < best[(u, v)]:
            best[(u, v)] = float(w)
    return best


def out_lists(n, best):
    out = {u: [] for u in range(n)}
    for (u, v), w in best.items():
        if u != v:
            out[u].append((v, w))
    return out


def negative_cycles_exist(n, edges, only_reachable_from=None):
    best = cheapest_pairs(edges)
    out = out_lists(n, best)
    allowed = set(range(n)) if only_reachable_from is None else reachable(n, edges, only_reachable_from)
    if any(u == v and w < 0 and u in allowed for (u, v), w in best.items()):
        return True
    for s in allowed:  # cycles whose smallest node is s
        stack = [(s, 0.0, {s})]
        while stack:
            u, total, used = stack.pop()
            for v, w in out[u]:
                if v == s and total + w < 0:
                    return True
                if v > s and v not in used:
                    stack.append((v, total + w, used | {v}))
    return False


def reachable(n, edges, src):
    out = {u: [] for u in range(n)}
    for u, v, _ in edges:
        out[u].append(v)
    seen, stack = {src}, [src]
    while stack:
        for v in out[stack.pop()]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def simple_path_distances(n, edges, src):
    out = out_lists(n, cheapest_pairs(edges))
    dist = [math.inf] * n
    on = [False] * n

    def walk(u, total):
        dist[u] = min(dist[u], total)
        on[u] = True
        for v, w in out[u]:
            if not on[v]:
                walk(v, total + w)
        on[u] = False

    walk(src, 0.0)
    return dist


def check_cycle(edges, cycle):
    assert isinstance(cycle, list) and cycle, f"expected a non-empty list of nodes, got {cycle!r}"
    assert len(set(cycle)) == len(cycle), f"a cycle visits each node once: {cycle}"
    best = cheapest_pairs(edges)
    total = 0.0
    for a, b in zip(cycle, cycle[1:] + cycle[:1]):
        assert (a, b) in best, f"{a} -> {b} isn't an edge, so {cycle} isn't a cycle"
        total += best[(a, b)]
    assert total < 0, f"the cycle {cycle} costs {total}, which isn't negative"


def random_graph(rnd, n, m, lo=-3, hi=8):
    return [(rnd.randrange(n), rnd.randrange(n), rnd.randint(lo, hi)) for _ in range(m)]


# ---------------------------------------------------------------------------
# bellman_ford
# ---------------------------------------------------------------------------
def test_negative_edge_that_fools_dijkstra():
    edges = [(0, 1, 2), (0, 2, 5), (2, 1, -4)]
    assert bellman_ford(3, wrap(edges), 0) == [0, 1, 5]


def test_single_node_and_unreachable():
    assert bellman_ford(1, [], 0) == [0]
    assert bellman_ford(3, wrap([(1, 2, -1)]), 0) == [0, math.inf, math.inf]


def test_reachable_negative_cycle_gives_none():
    assert bellman_ford(3, wrap([(0, 1, 1), (1, 2, 1), (2, 1, -3)]), 0) is None
    assert bellman_ford(2, wrap([(0, 1, 1), (1, 1, -1)]), 0) is None


def test_unreachable_negative_cycle_is_ignored():
    edges = [(0, 1, 4), (2, 3, 1), (3, 2, -5), (3, 1, 1)]  # 2 <-> 3 is negative, but 0 can't get there
    assert bellman_ford(4, wrap(edges), 0) == [0, 4, math.inf, math.inf]
    # A big lap, so a "large number" standing in for infinity (10**9, even 10**18) gets lowered too.
    edges = [(0, 1, 4), (2, 3, 1), (3, 2, -(10**6)), (3, 1, 1)]
    assert bellman_ford(4, wrap(edges), 0) == [0, 4, math.inf, math.inf]


def test_negative_cycle_far_behind_the_source():
    edges = [(i, i + 1, 1) for i in range(50)] + [(50, 48, -3)]  # 48 -> 49 -> 50 -> 48 costs -1
    assert bellman_ford(51, wrap(edges), 0) is None


def test_needs_all_v_minus_1_rounds():
    # A chain with its edges listed backwards: each round fixes one more node.
    n = 300
    edges = [(i, i + 1, -1) for i in reversed(range(n - 1))]
    with rounds_at_most(n + 1, edges):
        assert bellman_ford(n, wrap(edges), 0) == [-i for i in range(n)]


def test_random_small_graphs_against_brute_force():
    rnd = random.Random(808)
    nones = 0
    for _ in range(400):
        n = rnd.randint(1, 6)
        edges = random_graph(rnd, n, rnd.randint(0, 12))
        src = rnd.randrange(n)
        with rounds_at_most(n + 1, edges):
            got = bellman_ford(n, wrap(edges), src)
        if negative_cycles_exist(n, edges, only_reachable_from=src):
            assert got is None, f"a negative cycle is reachable from {src}: n={n}, edges={edges}"
            nones += 1
        else:
            assert got == simple_path_distances(n, edges, src), f"n={n}, edges={edges}, src={src}"
    assert 40 < nones < 360  # the generator makes both kinds


def layered_graph(seed, n, depth, extra):
    """Distances known by construction, negative edges included, no negative cycle.

    Every node v gets a value d[v] (negative ones too). Tree edges are tight,
    w = d[v] - d[parent], and every tree path from the source has at most
    `depth` edges. Every other edge has w >= d[v] - d[u], so it never helps:
    around any cycle the weights add up to at least 0.
    """
    rnd = random.Random(seed)
    d = [rnd.randint(-60, 60) for _ in range(n)]
    d[0] = 0
    layer = [0] + [1 + rnd.randrange(depth) for _ in range(n - 1)]
    by_layer = {k: [v for v in range(n) if layer[v] == k] for k in range(depth + 1)}
    edges = []
    for v in range(1, n):
        p = rnd.choice(by_layer[layer[v] - 1] or [0])  # a node one layer up
        edges.append((p, v, d[v] - d[p]))
    for _ in range(extra):
        u, v = rnd.randrange(n), rnd.randrange(n)
        edges.append((u, v, d[v] - d[u] + rnd.randrange(15)))
    rnd.shuffle(edges)
    return edges, d


def test_stops_as_soon_as_a_round_changes_nothing():
    n = 3000
    edges, d = layered_graph(5, n, depth=5, extra=12_000)
    assert sum(w < 0 for _, _, w in edges) > 1000  # plenty of negative edges
    with rounds_at_most(8, edges):  # 5 rounds to settle, 1 to notice; V - 1 = 2,999 is far too many
        assert bellman_ford(n, wrap(edges), 0) == d


def test_big_graph_with_a_negative_cycle_deep_inside():
    n = 1000
    edges, d = layered_graph(6, n, depth=5, extra=3000)
    a, b, c = 750, 850, 950
    edges += [(a, b, d[b] - d[a]), (b, c, d[c] - d[b]), (c, a, d[a] - d[c] - 1)]  # this lap costs -1
    assert bellman_ford(n, wrap(edges), 0) is None


# ---------------------------------------------------------------------------
# negative_cycle
# ---------------------------------------------------------------------------
def test_cycle_example():
    edges = [(0, 1, 1), (1, 2, 1), (2, 1, -3)]
    got = negative_cycle(3, wrap(edges))
    check_cycle(edges, got)
    assert sorted(got) == [1, 2]


def test_no_cycle_gives_none():
    assert negative_cycle(1, []) is None
    assert negative_cycle(3, wrap([(0, 1, -5), (1, 2, -5), (0, 2, 1)])) is None  # negative edges, no cycle
    assert negative_cycle(2, wrap([(0, 1, 3), (1, 0, -3)])) is None  # a lap of exactly 0


def test_negative_self_loop():
    edges = [(0, 1, 2), (2, 2, -1)]
    assert negative_cycle(3, wrap(edges)) == [2]


def test_cycle_node_0_cannot_reach():
    edges = [(0, 1, 1), (2, 3, 2), (3, 4, -1), (4, 2, -2), (4, 0, 7)]
    got = negative_cycle(5, wrap(edges))
    check_cycle(edges, got)
    assert sorted(got) == [2, 3, 4]


def test_cycle_random_small_graphs_against_brute_force():
    rnd = random.Random(809)
    found = 0
    for _ in range(400):
        n = rnd.randint(1, 6)
        edges = random_graph(rnd, n, rnd.randint(0, 12))
        with rounds_at_most(n + 2, edges):
            got = negative_cycle(n, wrap(edges))
        if negative_cycles_exist(n, edges):
            check_cycle(edges, got)
            found += 1
        else:
            assert got is None, f"no negative cycle exists, got {got}: n={n}, edges={edges}"
    assert 40 < found < 360


def test_big_cycle_in_one_run():
    # Nodes 0..339 have no negative cycle and can't reach the 60-node negative
    # ring at 340..399. One run finds the ring; a fresh run from each node in
    # turn spends hundreds of runs on the first 340 nodes before it gets there.
    rnd = random.Random(810)
    n, ring = 400, list(range(340, 400))
    d = [rnd.randint(-40, 40) for _ in range(n)]
    edges = []
    for _ in range(1400):
        u, v = rnd.randrange(340), rnd.randrange(340)
        edges.append((u, v, d[v] - d[u] + rnd.randrange(10)))  # never a negative lap
    for _ in range(200):
        u, v = rnd.choice(ring), rnd.randrange(n)  # the ring can reach the rest, not the other way
        edges.append((u, v, d[v] - d[u] + rnd.randrange(10)))
    rnd.shuffle(ring)
    for a, b in zip(ring, ring[1:]):
        edges.append((a, b, d[b] - d[a]))
    edges.append((ring[-1], ring[0], d[ring[0]] - d[ring[-1]] - 1))  # the lap costs -1
    rnd.shuffle(edges)
    with rounds_at_most(n + 2, edges):
        got = negative_cycle(n, wrap(edges))
    check_cycle(edges, got)


def test_big_cycle_in_one_run_whatever_the_start_order():
    # The negative ring sits in the middle (nodes 170..229) and nothing outside
    # it can reach it. Below it, nodes 0..169 only have edges down, and their
    # cheapest routes run down a chain i -> i-1 -> ... -> 0 (up to 169 edges,
    # listed so that each round moves one step); above it, nodes 230..399
    # mirror that upward. A run from each start in
    # turn, counting up or down, and even one that skips starts an earlier run
    # reached, does a long run for each of 170 starts before it meets the ring.
    rnd = random.Random(811)
    n = 400
    low, ring, high = list(range(170)), list(range(170, 230)), list(range(230, 400))
    d = [rnd.randint(-40, 40) for _ in range(n)]
    edges, chains = [], []
    for side, step in ((low, -1), (high, +1)):
        chain = [(b, a) if step < 0 else (a, b) for a, b in zip(side, side[1:])]
        if step > 0:
            chain.reverse()  # listed against the direction routes run: one step per round
        chains += [(u, v, d[v] - d[u]) for u, v in chain]  # the chain: tight
        for _ in range(700):
            u, v = rnd.sample(side, 2)
            if (v - u) * step < 0:
                u, v = v, u
            edges.append((u, v, d[v] - d[u] + 1 + rnd.randrange(10)))  # never a shortcut
    for _ in range(200):
        u, v = rnd.choice(ring), rnd.choice(low + high)  # the ring reaches out, nothing reaches in
        edges.append((u, v, d[v] - d[u] + rnd.randrange(10)))
    rnd.shuffle(ring)
    for a, b in zip(ring, ring[1:]):
        edges.append((a, b, d[b] - d[a]))
    edges.append((ring[-1], ring[0], d[ring[0]] - d[ring[-1]] - 1))  # the lap costs -1
    rnd.shuffle(edges)
    edges += chains
    with rounds_at_most(n + 2, edges):
        got = negative_cycle(n, wrap(edges))
    check_cycle(edges, got)
    assert sorted(got) == sorted(ring)
