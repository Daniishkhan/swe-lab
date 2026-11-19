import ast
import inspect
import random
import signal

import pytest

import clone_graph as cg
from clone_graph import Node, clone


@pytest.fixture(autouse=True)
def time_limit():
    """An O(V + E) clone of 100,000 nodes takes well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: is each 'already copied?' check scanning the copies made so far?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


@pytest.fixture
def made(monkeypatch):
    """Counts every Node created while the test runs."""
    count = [0]
    real = Node.__init__

    def counting_init(self, *a, **kw):
        count[0] += 1
        real(self, *a, **kw)

    monkeypatch.setattr(Node, "__init__", counting_init)
    return count


def build(vals, edges):
    """Original graph: node i has val vals[i] and edges (i, j) in list order."""
    nodes = [Node(v) for v in vals]
    for i, j in edges:
        nodes[i].neighbors.append(nodes[j])
    return nodes


def reachable(start):
    """How many original nodes the copy should have (the test's own count)."""
    seen, todo = {id(start)}, [start]
    while todo:
        for nb in todo.pop().neighbors:
            if id(nb) not in seen:
                seen.add(id(nb))
                todo.append(nb)
    return len(seen)


def check_copy(start, got):
    """The copy matches the original node by node and shares nothing with it."""
    assert got is not None and got is not start
    pair = {id(start): got}
    copies = {id(got)}
    todo = [start]
    while todo:
        o = todo.pop()
        c = pair[id(o)]
        assert type(c) is Node, "copies must be Nodes"
        assert c.val == o.val
        assert len(c.neighbors) == len(o.neighbors), f"node {o.val}: neighbor count"
        for on, cn in zip(o.neighbors, c.neighbors):
            if id(on) in pair:
                assert pair[id(on)] is cn, f"node {o.val}: a neighbor's copy must be the one copy of that node"
            else:
                assert id(cn) not in copies, "two original nodes share one copy"
                pair[id(on)] = cn
                copies.add(id(cn))
                todo.append(on)
    originals = set(pair)
    assert not (copies & originals), "the copy shares nodes with the original"
    return len(pair)


def snapshot(nodes):
    return [(n.val, [id(x) for x in n.neighbors], sorted(vars(n))) for n in nodes]


def test_example(made):
    a, b = build([1, 2], [(0, 1), (1, 0), (1, 1)])
    made[0] = 0
    c = clone(a)
    assert made[0] == 2
    assert c is not a and c.val == 1
    assert c.neighbors[0].val == 2
    assert c.neighbors[0].neighbors[0] is c
    assert c.neighbors[0].neighbors[1] is c.neighbors[0]
    assert a.neighbors == [b] and b.neighbors == [a, b]


def test_none_and_single():
    assert clone(None) is None
    a = Node(7)
    c = clone(a)
    assert c is not a and c.val == 7 and c.neighbors == [] and c.neighbors is not a.neighbors
    a.neighbors.append(a)
    c = clone(a)
    assert c.neighbors == [c] and c is not a


def test_same_vals_are_still_different_nodes(made):
    # every val is 0, so vals can't tell nodes apart
    nodes = build([0] * 5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (2, 2), (0, 1)])
    made[0] = 0
    got = clone(nodes[0])
    assert made[0] == 5, f"{made[0]} Nodes created for 5 originals"
    assert check_copy(nodes[0], got) == 5


def test_only_reachable_nodes_are_copied(made):
    nodes = build(list(range(6)), [(0, 1), (1, 0), (2, 0), (3, 4), (5, 5)])
    before = snapshot(nodes)
    made[0] = 0
    got = clone(nodes[0])
    assert made[0] == 2
    assert check_copy(nodes[0], got) == 2
    assert snapshot(nodes) == before, "don't change the original"


def test_random_graphs(made):
    rng = random.Random(5)
    for _ in range(300):
        n = rng.randint(1, 15)
        edges = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 3 * n))]
        nodes = build([rng.randint(0, 3) for _ in range(n)], edges)
        before = snapshot(nodes)
        start = rng.choice(nodes)
        want = reachable(start)
        made[0] = 0
        got = clone(start)
        assert made[0] == want, f"{made[0]} Nodes created for {want} reachable originals"
        assert check_copy(start, got) == want
        assert snapshot(nodes) == before, "don't change the original"


def test_long_chain_with_back_edges(made):
    n = 100_000
    # i -> i+1 makes a 100,000-deep path (recursion fails); i -> i // 2 adds cycles
    edges = [(i, i + 1) for i in range(n - 1)] + [(i, i // 2) for i in range(1, n)]
    nodes = build(list(range(n)), edges)
    made[0] = 0
    got = clone(nodes[0])
    assert made[0] == n
    assert check_copy(nodes[0], got) == n


def test_no_deepcopy_and_no_recursion_limit_tricks():
    tree = ast.parse(inspect.getsource(cg))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names |= {a.name.split(".")[-1] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert "deepcopy" not in names, "copy.deepcopy is the answer: build the copy yourself"
    assert "setrecursionlimit" not in names, "raising the recursion limit hides the problem: walk with your own stack"
