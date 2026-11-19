import random

import pytest

from min_heap import MinHeap, merge_k_sorted, top_k_frequent


def drain(h):
    out = []
    while len(h):
        out.append(h.pop())
    return out


def test_push_pop_sorted():
    rng = random.Random(7)
    data = [rng.randint(-100, 100) for _ in range(500)]
    h = MinHeap()
    for x in data:
        h.push(x)
    assert len(h) == 500
    assert drain(h) == sorted(data)


def test_peek_does_not_remove():
    h = MinHeap()
    h.push(5)
    h.push(1)
    assert h.peek() == 1
    assert len(h) == 2


def test_empty_raises():
    h = MinHeap()
    with pytest.raises(IndexError):
        h.pop()
    with pytest.raises(IndexError):
        h.peek()


def test_from_list():
    data = [9, 4, 7, 1, 8, 2, 2, 6]
    h = MinHeap.from_list(data)
    assert drain(h) == sorted(data)


def test_top_k_frequent():
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([4], 1) == [4]


def test_merge_k_sorted():
    assert merge_k_sorted([[1, 4, 5], [1, 3, 4], [2, 6]]) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_sorted([]) == []
    assert merge_k_sorted([[], [1], []]) == [1]
