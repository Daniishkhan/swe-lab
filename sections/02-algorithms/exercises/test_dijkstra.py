import math
import random
import signal

import pytest

from dijkstra import dijkstra, shortest_route


class TooMuchWork(AssertionError):
    pass


# ---------------------------------------------------------------------------
# Counting weights. Every edge weight is a W: a float that counts each time
# it is added to something (d + w or w + d). Correct Dijkstra adds each edge
# once when its start node is finalised (twice if it computes d + w twice).
# Past the budget, the next addition raises, so slow code fails fast.
# ---------------------------------------------------------------------------
class W(float):
    adds = 0
    limit = None

    @staticmethod
    def _tick():
        W.adds += 1
        if W.limit is not None and W.adds > W.limit:
            raise TooMuchWork(
                f"over {W.limit:,} additions of an edge weight: some edges are relaxed again and again "
                "(stale heap entries re-expanded? a Bellman-Ford style sweep over all edges?)"
            )

    def __add__(self, other):
        W._tick()
        return float.__add__(self, other)

    def __radd__(self, other):
        W._tick()
        return float.__radd__(self, other)


class adds_at_most:
    def __init__(self, limit):
        self.limit = limit

    def __enter__(self):
        W.adds, W.limit = 0, self.limit
        return self

    def __exit__(self, *exc):
        W.limit = None
        return False


def wrap(edges):
    return [(u, v, W(w)) for u, v, w in edges]


@pytest.fixture(autouse=True)
def time_limit(request):
    """Every test has a time cap (Unix only). The 60,000-node tests get 15 s."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is something scanning all V nodes to find the next one (O(V^2))?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(15 if "big" in request.node.name else 10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        W.limit = None


# ---------------------------------------------------------------------------
# Brute force for small graphs: try every simple path. With weights >= 0 a
# cheapest walk never needs to repeat a node, so this is the true answer.
# ---------------------------------------------------------------------------
def cheapest_pair_weights(n, edges):
    best = {}
    for u, v, w in edges:
        if u != v and ((u, v) not in best or w < best[(u, v)]):
            best[(u, v)] = float(w)
    return best


def brute_force(n, edges, src):
    best = cheapest_pair_weights(n, edges)
    out = {u: [] for u in range(n)}
    for (u, v), w in best.items():
        out[u].append((v, w))
    dist = [math.inf] * n
    on_path = [False] * n

    def walk(u, total):
        dist[u] = min(dist[u], total)
        on_path[u] = True
        for v, w in out[u]:
            if not on_path[v]:
                walk(v, total + w)
        on_path[u] = False

    walk(src, 0.0)
    return dist


def random_graph(rnd, n, m, wmax=9):
    return [(rnd.randrange(n), rnd.randrange(n), rnd.randrange(wmax + 1)) for _ in range(m)]


def check_route(n, edges, src, dst, got, expected_total):
    if expected_total == math.inf:
        assert got is None, f"{dst} can't be reached from {src}, so expected None, got {got!r}"
        return
    assert got is not None, f"expected a route of total {expected_total}, got None"
    total, path = got
    assert total == expected_total, f"total {total}, but the cheapest route costs {expected_total}"
    assert path[0] == src and path[-1] == dst, f"the path must run from {src} to {dst}: {path}"
    best = cheapest_pair_weights(n, edges)
    cost = 0.0
    for a, b in zip(path, path[1:]):
        assert (a, b) in best, f"the path uses {a} -> {b}, which isn't an edge"
        cost += best[(a, b)]
    assert cost == expected_total, f"the path {path} costs {cost}, not {expected_total}"


# ---------------------------------------------------------------------------
# dijkstra: small cases
# ---------------------------------------------------------------------------
EXAMPLE = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]


def test_example():
    with adds_at_most(2 * len(EXAMPLE)):
        assert dijkstra(5, wrap(EXAMPLE), 0) == [0, 3, 1, 4, math.inf]


def test_single_node():
    assert dijkstra(1, [], 0) == [0]


def test_edges_are_one_way():
    assert dijkstra(2, wrap([(1, 0, 1)]), 0) == [0, math.inf]


def test_zero_weights_parallel_edges_and_self_loops():
    edges = [(0, 1, 5), (0, 1, 2), (1, 2, 0), (2, 2, 0), (2, 0, 0)]
    assert dijkstra(3, wrap(edges), 0) == [0, 2, 2]


def test_source_in_the_middle():
    edges = [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, 1)]
    assert dijkstra(4, wrap(edges), 2) == [2, 3, 0, 1]


def test_fewest_edges_is_not_cheapest():
    # 0 -> 4 directly costs 10; the 4-edge route costs 4. BFS would say 1 edge.
    edges = [(0, 4, 10), (0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)]
    assert dijkstra(5, wrap(edges), 0) == [0, 1, 2, 3, 4]


def test_random_small_graphs_against_brute_force():
    rnd = random.Random(802)
    for _ in range(300):
        n = rnd.randint(1, 7)
        edges = random_graph(rnd, n, rnd.randint(0, 16))
        src = rnd.randrange(n)
        with adds_at_most(2 * len(edges) + 2):
            got = dijkstra(n, wrap(edges), src)
        assert got == brute_force(n, edges, src), f"n={n}, edges={edges}, src={src}"


def test_stale_heap_entries_are_skipped():
    # Nodes 1..k each give the hub a better distance than the last, so the hub
    # sits in the heap k times. The hub has d edges out. Expanding every copy
    # costs k * d relaxations; skipping the stale copies costs d.
    k = d = 300
    hub = k + 1
    edges = [(0, i, i) for i in range(1, k + 1)]
    edges += [(i, hub, 3 * k - 2 * i) for i in range(1, k + 1)]  # via i: 3k - i, best via k: 2k
    edges += [(hub, hub + 1 + j, 1) for j in range(d)]
    n = hub + 1 + d
    expected = [0] + list(range(1, k + 1)) + [2 * k] + [2 * k + 1] * d
    with adds_at_most(2 * len(edges)):
        assert dijkstra(n, wrap(edges), 0) == expected


# ---------------------------------------------------------------------------
# Big graphs, built so that the answer is known by construction: every node
# gets a distance first, tree edges are tight (w = d[v] - d[parent]) and
# every other edge is at least as long as the gap it spans, so it can never
# make a shortcut. A block of nodes can't be reached at all.
# ---------------------------------------------------------------------------
def constructed_graph(seed, n_reach, n_cut, extra):
    rnd = random.Random(seed)
    n = n_reach + n_cut
    nodes = list(range(n))
    rnd.shuffle(nodes)
    reach, cut = nodes[:n_reach], nodes[n_reach:]
    dist = [math.inf] * n
    dist[reach[0]] = 0
    edges = []
    for i in range(1, n_reach):
        v = reach[i]
        dist[v] = dist[reach[i - 1]] + rnd.randrange(4)  # never decreasing along `reach`
        p = reach[rnd.randrange(max(0, i - 40), i)]  # a parent that comes earlier
        edges.append((p, v, dist[v] - dist[p]))
    for _ in range(extra):
        u, v = rnd.choice(reach), rnd.choice(reach)
        edges.append((u, v, max(0, dist[v] - dist[u]) + rnd.randrange(30)))
    for _ in range(n_cut * 2):  # unreachable block: edges among cut nodes, and out of it
        u = rnd.choice(cut)
        v = rnd.choice(cut) if rnd.random() < 0.5 else rnd.choice(reach)
        edges.append((u, v, rnd.randrange(30)))
    rnd.shuffle(edges)
    return n, edges, reach, dist


def test_big_sparse_graph():
    n, edges, reach, expected = constructed_graph(8, 56_000, 4_000, 120_000)
    with adds_at_most(2 * len(edges)):
        got = dijkstra(n, wrap(edges), reach[0])
    assert got == expected


# ---------------------------------------------------------------------------
# shortest_route
# ---------------------------------------------------------------------------
def test_route_example():
    check_route(5, EXAMPLE, 0, 3, shortest_route(5, wrap(EXAMPLE), 0, 3), 4)


def test_route_to_itself_and_unreachable():
    assert shortest_route(3, wrap([(0, 1, 2)]), 1, 1) == (0, [1])
    assert shortest_route(3, wrap([(0, 1, 2)]), 0, 2) is None
    assert shortest_route(3, wrap([(0, 1, 2)]), 1, 0) is None


def test_route_is_not_final_when_first_discovered():
    # 0 discovers 3 at cost 10 straight away; the real answer, 3, comes later.
    edges = [(0, 3, 10), (0, 1, 1), (1, 2, 1), (2, 3, 1)]
    check_route(4, edges, 0, 3, shortest_route(4, wrap(edges), 0, 3), 3)


def test_route_random_small_graphs():
    rnd = random.Random(803)
    for _ in range(300):
        n = rnd.randint(1, 7)
        edges = random_graph(rnd, n, rnd.randint(0, 16))
        src, dst = rnd.randrange(n), rnd.randrange(n)
        with adds_at_most(2 * len(edges) + 2):
            got = shortest_route(n, wrap(edges), src, dst)
        check_route(n, edges, src, dst, got, brute_force(n, edges, src)[dst])


def test_big_route_stops_once_the_goal_is_final():
    n, edges, reach, dist = constructed_graph(9, 56_000, 4_000, 120_000)
    src, dst = reach[0], reach[150]
    out_degree = [0] * n
    for u, _, _ in edges:
        out_degree[u] += 1
    # Only nodes no farther than dst can be finalised before it.
    budget = 2 * sum(out_degree[v] for v in reach if dist[v] <= dist[dst]) + 2
    with adds_at_most(budget):
        got = shortest_route(n, wrap(edges), src, dst)
    check_route(n, edges, src, dst, got, dist[dst])
