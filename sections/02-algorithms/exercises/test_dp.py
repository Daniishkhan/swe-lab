from dp import edit_distance, knapsack_01, lis_length


def test_edit_distance():
    assert edit_distance("horse", "ros") == 3
    assert edit_distance("intention", "execution") == 5
    assert edit_distance("", "abc") == 3
    assert edit_distance("same", "same") == 0


def test_lis_length():
    assert lis_length([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert lis_length([0, 1, 0, 3, 2, 3]) == 4
    assert lis_length([7, 7, 7, 7]) == 1
    assert lis_length([]) == 0


def test_knapsack_01():
    assert knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7) == 9
    assert knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 0) == 0
    assert knapsack_01([], [], 10) == 0
    assert knapsack_01([5], [10], 4) == 0
