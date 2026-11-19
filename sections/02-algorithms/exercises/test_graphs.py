from graphs import count_components, topological_sort


def assert_valid_order(n, edges, order):
    assert order is not None
    assert sorted(order) == list(range(n))
    pos = {node: i for i, node in enumerate(order)}
    for u, v in edges:
        assert pos[u] < pos[v], f"{u} must come before {v}"


def test_topo_dag():
    edges = [(5, 2), (5, 0), (4, 0), (4, 1), (2, 3), (3, 1)]
    assert_valid_order(6, edges, topological_sort(6, edges))


def test_topo_no_edges():
    assert_valid_order(3, [], topological_sort(3, []))


def test_topo_cycle():
    assert topological_sort(3, [(0, 1), (1, 2), (2, 0)]) is None
    assert topological_sort(2, [(1, 1)]) is None


def test_topo_long_chain():
    n = 5000
    edges = [(i, i + 1) for i in range(n - 1)]
    assert topological_sort(n, edges) == list(range(n))


def test_components():
    assert count_components(5, [(0, 1), (1, 2), (3, 4)]) == 2
    assert count_components(5, []) == 5
    assert count_components(1, []) == 1
    assert count_components(4, [(0, 1), (1, 0), (2, 3), (3, 2)]) == 2
