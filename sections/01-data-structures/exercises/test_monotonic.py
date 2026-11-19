from monotonic import next_greater, sliding_window_max


def test_next_greater():
    assert next_greater([2, 1, 2, 4, 3]) == [4, 2, 4, -1, -1]
    assert next_greater([5, 4, 3]) == [-1, -1, -1]
    assert next_greater([]) == []
    assert next_greater([1, 1, 1]) == [-1, -1, -1]


def test_sliding_window_max():
    assert sliding_window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_window_max([4], 1) == [4]
    assert sliding_window_max([], 3) == []
    assert sliding_window_max([9, 8, 7, 6], 2) == [9, 8, 7]
