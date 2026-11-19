from union_find import UnionFind


def test_initially_disjoint():
    uf = UnionFind(5)
    assert uf.components == 5
    assert not uf.connected(0, 1)
    assert uf.find(3) == 3


def test_union_and_connected():
    uf = UnionFind(6)
    assert uf.union(0, 1) is True
    assert uf.union(1, 2) is True
    assert uf.union(0, 2) is False
    assert uf.connected(0, 2)
    assert not uf.connected(0, 3)
    assert uf.components == 4


def test_transitive_chain():
    n = 10_000
    uf = UnionFind(n)
    for i in range(n - 1):
        uf.union(i, i + 1)
    assert uf.components == 1
    assert uf.connected(0, n - 1)
    assert uf.find(0) == uf.find(n - 1)
