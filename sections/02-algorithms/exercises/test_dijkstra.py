import math

from dijkstra import dijkstra


def test_basic():
    edges = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]
    assert dijkstra(5, edges, 0) == [0, 3, 1, 4, math.inf]


def test_single_node():
    assert dijkstra(1, [], 0) == [0]


def test_directed():
    assert dijkstra(2, [(1, 0, 1)], 0) == [0, math.inf]


def test_zero_weight_and_parallel_edges():
    edges = [(0, 1, 5), (0, 1, 2), (1, 2, 0)]
    assert dijkstra(3, edges, 0) == [0, 2, 2]
