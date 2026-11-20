import random
from collections import deque

import pytest

from graphs import count_islands, find_cycle, semester_plan, shortest_path, steps_to_exit


class TooMuchWork(AssertionError):
    pass


# ---------------------------------------------------------------------------
# Counting helpers. Graph nodes count every hash (every dict or set lookup,
# insert and `in` check). Grid rows count every cell read. Both give up early
# past a budget, so a slow solution fails fast instead of hanging.
# ---------------------------------------------------------------------------
class Node:
    """A hashable graph node that counts how often it is hashed. Equal only to itself."""

    __slots__ = ("name", "_h")
    hashes = 0
    limit = None

    def __init__(self, name):
        self.name = name
        self._h = hash(name)

    def __hash__(self):
        Node.hashes += 1
        if Node.limit is not None and Node.hashes > Node.limit:
            raise TooMuchWork(f"over {Node.limit:,} dict/set operations: something does more than O(V + E) work")
        return self._h

    def __repr__(self):
        return f"Node({self.name!r})"


class hashes_at_most:
    """with hashes_at_most(n): ... fails the test if the block hashes nodes more than n times."""

    def __init__(self, limit):
        self.limit = limit

    def __enter__(self):
        Node.hashes, Node.limit = 0, self.limit
        return self

    def __exit__(self, *exc):
        Node.limit = None
        return False


def to_nodes(graph):
    """Copy a {name: [names]} graph into one made of counting Nodes. Returns (graph, name -> Node)."""
    node = {name: Node(name) for name in graph}
    return {node[a]: [node[b] for b in nbrs] for a, nbrs in graph.items()}, node


def names(nodes):
    return None if nodes is None else [x.name for x in nodes]


class Row(list):
    """One grid row. Counts every cell read and refuses writes."""

    reads = 0
    limit = None

    def _tick(self, k=1):
        Row.reads += k
        if Row.limit is not None and Row.reads > Row.limit:
            raise TooMuchWork(f"over {Row.limit:,} cell reads: something reads cells far more than a few times each")

    def __getitem__(self, i):
        v = list.__getitem__(self, i)
        self._tick(len(v) if isinstance(i, slice) else 1)
        return v

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __contains__(self, x):
        self._tick(len(self))
        return list.__contains__(self, x)

    def __setitem__(self, i, v):
        raise TypeError("don't change the grid: keep your own visited marks")


def counted_grid(rows, reads_per_cell):
    grid = [Row(r) for r in rows]
    Row.reads = 0
    Row.limit = reads_per_cell * max(1, sum(len(r) for r in rows))
    return grid


@pytest.fixture(autouse=True)
def _reset_counters():
    yield
    Node.limit = None
    Row.limit = None


# Shared random graph makers (seeded by each test)
def random_undirected(rnd, n, p):
    g = {str(i): [] for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if rnd.random() < p:
                g[str(i)].append(str(j))
                g[str(j)].append(str(i))
    return g


def grid_graph(rows, cols):
    """rows x cols lattice as an undirected graph: node "r,c" joined to its 4 neighbours."""
    g = {}
    for r in range(rows):
        for c in range(cols):
            g[f"{r},{c}"] = [f"{r + dr},{c + dc}" for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                             if 0 <= r + dr < rows and 0 <= c + dc < cols]
    return g


def size(graph):
    return len(graph) + sum(len(v) for v in graph.values())


# ===========================================================================
# 4. shortest_path
# ===========================================================================
EXAMPLE = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"], "D": ["B", "C", "E"], "E": ["D"]}


def brute_distance(graph, start, goal):
    """Relax every edge V times (slow, but easy to trust)."""
    dist = {start: 0}
    for _ in range(len(graph)):
        for u in list(dist):
            for v in graph[u]:
                if dist[u] + 1 < dist.get(v, float("inf")):
                    dist[v] = dist[u] + 1
    return dist.get(goal)


def assert_shortest(graph, start, goal, path):
    want = brute_distance(graph, start, goal)
    if want is None:
        assert path is None, f"{goal!r} can't be reached from {start!r}: return None"
        return
    assert path is not None, f"{goal!r} is reachable from {start!r} in {want} steps"
    assert path[0] == start and path[-1] == goal, "the path must start at start and end at goal"
    for a, b in zip(path, path[1:]):
        assert b in graph[a], f"{a!r} -> {b!r} is not an edge"
    assert len(path) - 1 == want, f"path has {len(path) - 1} steps, the shortest has {want}"


def test_shortest_path_example():
    assert shortest_path(EXAMPLE, "A", "E") in (["A", "B", "D", "E"], ["A", "C", "D", "E"])
    assert shortest_path(EXAMPLE, "E", "A") in (["E", "D", "B", "A"], ["E", "D", "C", "A"])


def test_shortest_path_small_cases():
    assert shortest_path({"A": []}, "A", "A") == ["A"]
    assert shortest_path(EXAMPLE, "C", "C") == ["C"]
    assert shortest_path({"A": ["B"], "B": ["A"]}, "A", "B") == ["A", "B"]
    two_parts = {"A": ["B"], "B": ["A"], "C": ["D"], "D": ["C"]}
    assert shortest_path(two_parts, "A", "D") is None
    assert shortest_path({"A": [], "B": []}, "A", "B") is None
    messy = {"A": ["A", "B", "B"], "B": ["A", "A", "C"], "C": ["B", "C"]}   # self-loops, repeated edges
    assert shortest_path(messy, "A", "C") == ["A", "B", "C"]


def test_shortest_path_matches_brute_force():
    rnd = random.Random(21)
    for _ in range(150):
        g = random_undirected(rnd, rnd.randint(1, 12), rnd.choice([0.1, 0.25, 0.5]))
        nodes = list(g)
        start, goal = rnd.choice(nodes), rnd.choice(nodes)
        assert_shortest(g, start, goal, shortest_path(g, start, goal))


@pytest.mark.parametrize("goal", ["29,29", "far"])
def test_shortest_path_is_linear(goal):
    g = grid_graph(30, 30)            # 900 nodes, 3,480 neighbour entries
    g["far"] = []                     # an island nobody can reach: forces a full search
    expected = brute_distance(g, "0,0", goal)
    graph, node = to_nodes(g)
    budget = 20 * size(g)
    with hashes_at_most(budget):
        path = shortest_path(graph, node["0,0"], node[goal])
    assert_shortest(g, "0,0", goal, names(path))
    assert expected in (None, 58)


# ===========================================================================
# 5. count_islands
# ===========================================================================
def brute_islands(rows):
    """Give every land cell its own label, then spread the smallest label until nothing changes.
    Every pass rereads the grid, so it needs one pass per step a label travels: far too slow
    (and far over the read budget) for the big tests."""
    R = len(rows)
    C = len(rows[0]) if R else 0
    label = {(r, c): r * C + c for r in range(R) for c in range(C) if rows[r][c] == "1"}
    changed = True
    while changed:
        changed = False
        for (r, c) in list(label):
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < R and 0 <= nc < C and rows[nr][nc] == "1" and label[(nr, nc)] < label[(r, c)]:
                    label[(r, c)] = label[(nr, nc)]
                    changed = True
    return len(set(label.values()))


def test_count_islands_examples():
    one = ["11110",
           "11010",
           "11000",
           "00000"]
    three = ["11000",
             "11000",
             "00100",
             "00011"]
    assert count_islands(one) == 1
    assert count_islands(three) == 3


def test_count_islands_edges():
    assert count_islands([]) == 0
    assert count_islands([""]) == 0
    assert count_islands(["0"]) == 0
    assert count_islands(["1"]) == 1
    assert count_islands(["000", "000"]) == 0
    assert count_islands(["111", "111"]) == 1
    assert count_islands(["101", "010", "101"]) == 5, "diagonal cells are NOT connected"
    assert count_islands(["1", "0", "1", "1"]) == 2
    assert count_islands(["10101"]) == 3
    ring = ["111",
            "101",
            "111"]
    assert count_islands(ring) == 1, "a ring with a lake in the middle is still one island"


def test_count_islands_matches_brute_force_and_leaves_grid():
    rnd = random.Random(31)
    for _ in range(150):
        R, C = rnd.randint(1, 9), rnd.randint(1, 9)
        p = rnd.choice([0.3, 0.5, 0.7])
        rows = ["".join("1" if rnd.random() < p else "0" for _ in range(C)) for _ in range(R)]
        grid = [Row(r) for r in rows]
        Row.limit = None
        assert count_islands(grid) == brute_islands(rows)
        assert ["".join(list.__iter__(r)) for r in grid] == rows


def test_count_islands_is_linear():
    rnd = random.Random(32)
    rows = ["".join("1" if rnd.random() < 0.8 else "0" for _ in range(120)) for _ in range(120)]
    want = brute_islands(rows)
    grid = counted_grid(rows, reads_per_cell=10)
    assert count_islands(grid) == want


def snake(R, C):
    """Every even row is land; odd rows have one land cell, alternating ends. One island, one long path."""
    rows = []
    for r in range(R):
        if r % 2 == 0:
            rows.append("1" * C)
        else:
            end = C - 1 if r % 4 == 1 else 0
            rows.append("".join("1" if c == end else "0" for c in range(C)))
    return rows


def test_count_islands_long_winding_island():
    rows = snake(121, 120)            # one island of 7,380 cells, a single path end to end
    grid = counted_grid(rows, reads_per_cell=10)
    try:
        got = count_islands(grid)
    except RecursionError:
        pytest.fail("RecursionError: a recursive flood fill goes 7,000+ calls deep here. Use an explicit stack or a queue.")
    assert got == 1


# ===========================================================================
# 6. steps_to_exit
# ===========================================================================
def brute_steps(rows):
    """A separate BFS from every open cell (fine for tiny grids, far too slow for big ones)."""
    R = len(rows)
    C = len(rows[0]) if R else 0
    out = [[-1] * C for _ in range(R)]
    for r in range(R):
        for c in range(C):
            if rows[r][c] == "#":
                continue
            seen, q = {(r, c)}, deque([((r, c), 0)])
            while q:
                (y, x), d = q.popleft()
                if rows[y][x] == "E":
                    out[r][c] = d
                    break
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < R and 0 <= nx < C and rows[ny][nx] != "#" and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        q.append(((ny, nx), d + 1))
    return out


def test_steps_to_exit_example():
    rows = ["E..#",
            "..#.",
            "#...",
            "...E"]
    assert steps_to_exit(rows) == [[0, 1, 2, -1],
                                   [1, 2, -1, 2],
                                   [-1, 3, 2, 1],
                                   [3, 2, 1, 0]]


def test_steps_to_exit_edges():
    assert steps_to_exit([]) == []
    assert steps_to_exit(["E"]) == [[0]]
    assert steps_to_exit(["#"]) == [[-1]]
    assert steps_to_exit(["..."]) == [[-1, -1, -1]], "no exit anywhere: every cell is -1"
    assert steps_to_exit([".#E"]) == [[-1, -1, 0]], "a wall cuts the first cell off"
    assert steps_to_exit(["E.....E"]) == [[0, 1, 2, 3, 2, 1, 0]], "each cell counts its NEAREST exit"
    assert steps_to_exit(["EE", "EE"]) == [[0, 0], [0, 0]]


def test_steps_to_exit_matches_brute_force():
    rnd = random.Random(41)
    for _ in range(120):
        R, C = rnd.randint(1, 8), rnd.randint(1, 8)
        rows = ["".join(rnd.choices(".#E", weights=[7, 2, 1])[0] for _ in range(C)) for _ in range(R)]
        assert steps_to_exit(rows) == brute_steps(rows)


def test_steps_to_exit_is_linear_with_many_exits():
    rnd = random.Random(42)
    R = C = 80
    cells = [["#" if rnd.random() < 0.2 else "." for _ in range(C)] for _ in range(R)]
    for _ in range(300):             # 300 exits scattered around
        cells[rnd.randrange(R)][rnd.randrange(C)] = "E"
    rows = ["".join(r) for r in cells]
    want = brute_steps(rows)
    grid = counted_grid(rows, reads_per_cell=10)
    assert steps_to_exit(grid) == want


# ===========================================================================
# 7. find_cycle (directed)
# ===========================================================================
def brute_has_cycle(graph):
    """A cycle exists if some node can get back to itself."""
    for s in graph:
        seen, stack = set(), list(graph[s])
        while stack:
            u = stack.pop()
            if u == s:
                return True
            if u not in seen:
                seen.add(u)
                stack.extend(graph[u])
    return False


def assert_cycle(graph, cyc):
    assert cyc is not None, "this graph has a cycle"
    assert len(cyc) >= 1
    assert len(set(cyc)) == len(cyc), f"a cycle lists each node once: {cyc}"
    for a, b in zip(cyc, cyc[1:] + cyc[:1]):
        assert b in graph[a], f"{a!r} -> {b!r} is not an edge, so {cyc} is not a cycle"


DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


def test_find_cycle_none_on_diamond():
    assert find_cycle(DIAMOND) is None, (
        "A->B->D and A->C->D both reach D, but nothing leads back: no cycle. "
        "Reaching a FINISHED node again is fine; only a node on the current path means a cycle.")


def test_find_cycle_examples():
    assert find_cycle({}) is None
    assert find_cycle({"A": []}) is None
    assert find_cycle({"A": ["A"]}) == ["A"]
    g = {"A": ["B"], "B": ["C"], "C": ["A"]}
    assert_cycle(g, find_cycle(g))
    two = {"A": ["B"], "B": ["A"]}
    assert_cycle(two, find_cycle(two))
    tail = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["B"]}       # A leads into the cycle but isn't on it
    cyc = find_cycle(tail)
    assert_cycle(tail, cyc)
    assert "A" not in cyc


def test_find_cycle_cross_edges_are_not_cycles():
    # Searches started from different nodes meet at finished nodes: still no cycle.
    g = {"A": ["B"], "B": [], "C": ["A", "B"], "D": ["C", "B"], "E": ["D", "A"]}
    assert find_cycle(g) is None
    late = {"A": ["B"], "B": [], "C": ["D"], "D": ["E"], "E": ["C"]}  # the cycle is only reachable from C
    assert_cycle(late, find_cycle(late))


def test_find_cycle_matches_brute_force():
    rnd = random.Random(51)
    for _ in range(200):
        n = rnd.randint(1, 9)
        g = {str(i): [] for i in range(n)}
        for _ in range(rnd.randint(0, 2 * n)):
            g[str(rnd.randrange(n))].append(str(rnd.randrange(n)))
        cyc = find_cycle(g)
        if brute_has_cycle(g):
            assert_cycle(g, cyc)
        else:
            assert cyc is None, f"no cycle in {g}, got {cyc}"


def random_dag(rnd, n, m):
    order = [str(i) for i in range(n)]
    rnd.shuffle(order)
    g = {v: [] for v in order}
    for _ in range(m):
        i, j = sorted(rnd.sample(range(n), 2))
        g[order[i]].append(order[j])
    return g, order


def test_find_cycle_is_linear():
    rnd = random.Random(52)
    g, order = random_dag(rnd, 3000, 9000)
    graph, node = to_nodes(g)
    with hashes_at_most(20 * size(g)):
        assert find_cycle(graph) is None
    g[order[2900]].append(order[100])   # one back edge: now there is a cycle somewhere
    graph, node = to_nodes(g)
    with hashes_at_most(20 * size(g)):
        cyc = find_cycle(graph)
    assert_cycle(g, names(cyc))


def test_find_cycle_long_chain():
    n = 5000
    g = {str(i): [str(i + 1)] for i in range(n - 1)}
    g[str(n - 1)] = ["0"]                # one cycle through all 5,000 nodes
    graph, node = to_nodes(g)
    try:
        with hashes_at_most(20 * size(g)):
            cyc = find_cycle(graph)
    except RecursionError:
        pytest.fail("RecursionError: a recursive DFS goes 5,000 calls deep here. Keep your own stack.")
    assert_cycle(g, names(cyc))
    assert len(cyc) == n


# ===========================================================================
# 8. semester_plan
# ===========================================================================
def brute_plan(courses, prereqs):
    """Semester of a course = 1 + the latest semester of its prerequisites. Relax until stable.
    Each pass can push a level only as far as the pairs' order allows, so pairs listed
    back to front need one pass per semester: the long-chain test rejects it."""
    level = {c: 0 for c in courses}
    for _ in range(len(courses) + 1):
        changed = False
        for a, b in prereqs:
            if level[a] + 1 > level[b]:
                level[b] = level[a] + 1
                changed = True
        if not changed:
            break
    else:
        return None
    if any(v >= len(courses) for v in level.values()):
        return None
    plan = [set() for _ in range(max(level.values(), default=-1) + 1)]
    for c, v in level.items():
        plan[v].add(c)
    return plan


def as_sets(plan):
    return None if plan is None else [set(s) for s in plan]


def test_semester_plan_example():
    courses = ["intro", "data", "algo", "web", "ml"]
    prereqs = [("intro", "data"), ("intro", "web"), ("data", "algo"), ("data", "ml"), ("algo", "ml")]
    assert as_sets(semester_plan(courses, prereqs)) == [{"intro"}, {"data", "web"}, {"algo"}, {"ml"}]


def test_semester_plan_edges():
    assert semester_plan([], []) == []
    assert as_sets(semester_plan(["a", "b", "c"], [])) == [{"a", "b", "c"}], "no prerequisites: one semester"
    assert semester_plan(["a", "b"], [("a", "b"), ("b", "a")]) is None
    assert semester_plan(["a"], [("a", "a")]) is None, "a course that needs itself can never be taken"
    assert as_sets(semester_plan(["a", "b"], [("a", "b"), ("a", "b")])) == [{"a"}, {"b"}], "repeated pairs"
    # a cycle downstream: x and y are fine, but p, q (cycle) and r (needs q) can never be taken
    assert semester_plan(["x", "y", "p", "q", "r"], [("x", "y"), ("y", "p"), ("p", "q"), ("q", "p"), ("q", "r")]) is None


def test_semester_plan_matches_brute_force():
    rnd = random.Random(61)
    for _ in range(200):
        n = rnd.randint(0, 9)
        courses = [f"c{i}" for i in range(n)]
        prereqs = []
        for _ in range(rnd.randint(0, 2 * n) if n else 0):
            a, b = rnd.randrange(n), rnd.randrange(n)
            if rnd.random() < 0.85 and a > b:
                a, b = b, a                  # mostly forward pairs, so many cases have no cycle
            prereqs.append((courses[a], courses[b]))
        assert as_sets(semester_plan(courses, prereqs)) == brute_plan(courses, prereqs)


def test_semester_plan_long_chain_is_linear():
    n = 3000                                 # 3,000 semesters, one course each
    names_ = [f"c{i}" for i in range(n)]
    node = {s: Node(s) for s in names_}
    courses = [node[s] for s in names_]
    prereqs = [(courses[i], courses[i + 1]) for i in reversed(range(n - 1))]   # last pair first
    with hashes_at_most(20 * (n + len(prereqs))):
        plan = semester_plan(courses, prereqs)
    assert plan is not None and [names(s) for s in plan] == [[s] for s in names_]


def test_semester_plan_wide_is_linear():
    rnd = random.Random(62)
    g, order = random_dag(rnd, 2000, 8000)
    pairs = [(a, b) for a in g for b in g[a]]
    rnd.shuffle(pairs)
    want = brute_plan(list(g), pairs)
    node = {s: Node(s) for s in g}
    with hashes_at_most(20 * (len(g) + len(pairs))):
        plan = semester_plan([node[s] for s in g], [(node[a], node[b]) for a, b in pairs])
    assert [set(names(s)) for s in plan] == want
