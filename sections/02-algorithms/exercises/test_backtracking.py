import itertools

from backtracking import count_n_queens, permutations, subsets


def normalize(lists):
    return sorted(sorted(x) for x in lists)


def test_subsets():
    assert normalize(subsets([1, 2, 3])) == normalize(
        [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]
    )
    assert subsets([]) == [[]]


def test_permutations():
    got = sorted(tuple(p) for p in permutations([1, 2, 3]))
    assert got == sorted(itertools.permutations([1, 2, 3]))
    assert len(permutations([1, 2, 3, 4, 5])) == 120


def test_n_queens():
    assert count_n_queens(1) == 1
    assert count_n_queens(2) == 0
    assert count_n_queens(4) == 2
    assert count_n_queens(8) == 92
