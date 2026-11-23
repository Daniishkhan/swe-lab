import itertools
import random
import signal
from contextlib import contextmanager

import pytest

from py_toolkit import count_in_ranges, group_anagrams, round_robin, top_k_frequent


@contextmanager
def cap(seconds, hint):
    """Fail fast when the slow approach is used (Unix only; elsewhere no cap)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError(f"over {seconds} s: {hint}")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------- top_k_frequent

def test_top_k_example():
    assert top_k_frequent(["b", "a", "b", "c", "a", "b"], 2) == [("b", 3), ("a", 2)]


def test_top_k_ties_alphabetical():
    words = ["pear", "fig", "apple", "fig", "pear", "apple", "kiwi"]
    assert top_k_frequent(words, 3) == [("apple", 2), ("fig", 2), ("pear", 2)]


def test_top_k_small_cases():
    assert top_k_frequent([], 3) == []
    assert top_k_frequent(["x", "y"], 0) == []
    assert top_k_frequent(["x", "y"], -1) == []
    assert top_k_frequent(["x", "y", "x"], 10) == [("x", 2), ("y", 1)]


def test_top_k_670k_words():
    # 10 "top" words with known counts (two of them tied), then 60,000 rare
    # words appearing 1 to 20 times each, all shuffled together.
    rng = random.Random(10)
    top = {f"top{i}": 5000 - 300 * i for i in range(10)}
    top["top3b"] = top["top3"]  # a tie: "top3" < "top3b" alphabetically
    words = [w for w, c in top.items() for _ in range(c)]
    for i in range(60_000):
        words += [f"rare{i:05d}"] * rng.randint(1, 20)
    rng.shuffle(words)
    assert len(words) > 600_000
    with cap(5, "is something scanning all the words once per distinct word (list.count)?"):
        got = top_k_frequent(words, 5)
    assert got == [("top0", 5000), ("top1", 4700), ("top2", 4400), ("top3", 4100), ("top3b", 4100)]


# ---------------------------------------------------------------- group_anagrams

def test_group_anagrams_example():
    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [
        ["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]


def test_group_anagrams_edges():
    assert group_anagrams([]) == []
    assert group_anagrams([""]) == [[""]]
    assert group_anagrams(["ab", "ba", "ab"]) == [["ab", "ba", "ab"]]
    # same letters, different counts: not anagrams
    assert group_anagrams(["aab", "abb", "bab"]) == [["aab"], ["abb", "bab"]]


def test_group_anagrams_many():
    # 40,000 distinct letter sets (5-letter combinations), 3 orderings of each.
    rng = random.Random(20)
    tagged = []
    for gid, combo in enumerate(itertools.islice(itertools.combinations("abcdefghijklmnopqrstuvwxyz", 5), 40_000)):
        letters = list(combo)
        for _ in range(3):
            rng.shuffle(letters)
            tagged.append((gid, "".join(letters)))
    rng.shuffle(tagged)
    expected, where = [], {}
    for gid, w in tagged:  # by construction: we know each word's group id
        if gid not in where:
            where[gid] = len(expected)
            expected.append([])
        expected[where[gid]].append(w)
    words = [w for _, w in tagged]
    with cap(5, "are you comparing each word with every group or every other word?"):
        got = group_anagrams(words)
    assert got == expected


# ---------------------------------------------------------------- round_robin

def test_round_robin_example():
    assert round_robin([("a", 3), ("b", 1), ("c", 5)], 2) == ["b", "a", "c"]


def test_round_robin_edges():
    assert round_robin([], 3) == []
    assert round_robin([("solo", 10)], 3) == ["solo"]
    assert round_robin([("a", 2), ("b", 2)], 100) == ["a", "b"]
    assert round_robin([("a", 4), ("b", 1), ("c", 4)], 1) == ["b", "a", "c"]
    with pytest.raises(ValueError):
        round_robin([("a", 1)], 0)


def test_round_robin_does_not_change_input():
    jobs = [("a", 3), ("b", 1)]
    round_robin(jobs, 2)
    assert jobs == [("a", 3), ("b", 1)]


def test_round_robin_300k_jobs():
    # Each job needs 1, 2 or 3 turns. With everyone waiting from the start,
    # jobs that need r turns finish during pass r, in their arrival order.
    rng = random.Random(30)
    q = 10
    turns = [rng.randint(1, 3) for _ in range(300_000)]
    jobs = [(f"j{i}", (t - 1) * q + rng.randint(1, q)) for i, t in enumerate(turns)]
    expected = [f"j{i}" for r in (1, 2, 3) for i, t in enumerate(turns) if t == r]
    with cap(5, "is the queue a list with pop(0) or insert(0, …)? Each of those shifts every item."):
        got = round_robin(jobs, q)
    assert got == expected


# ---------------------------------------------------------------- count_in_ranges

def test_count_in_ranges_example():
    assert count_in_ranges([5, 1, 9, 5], [(1, 5), (6, 8), (0, 100)]) == [3, 0, 4]


def test_count_in_ranges_edges():
    assert count_in_ranges([], [(0, 10)]) == [0]
    assert count_in_ranges([3, 3, 3], []) == []
    assert count_in_ranges([3, 3, 3], [(3, 3), (4, 2), (-5, 2), (4, 9)]) == [3, 0, 0, 0]
    assert count_in_ranges([-4, 0, 7], [(-4, -4), (-10, 0), (1, 7)]) == [1, 2, 1]


def test_count_in_ranges_does_not_change_values():
    values = [9, 2, 7, 2]
    count_in_ranges(values, [(0, 5)])
    assert values == [9, 2, 7, 2]


def test_count_in_ranges_100k_by_100k():
    # values: every integer 0..49,999 exactly twice, shuffled. So the answer
    # for [lo, hi] is 2 × (how many integers of 0..49,999 are in it).
    rng = random.Random(40)
    values = list(range(50_000)) * 2
    rng.shuffle(values)
    queries, expected = [], []
    for _ in range(100_000):
        lo = rng.randint(-1000, 51_000)
        hi = lo + rng.randint(-10, 30_000)
        queries.append((lo, hi))
        expected.append(2 * max(0, min(hi, 49_999) - max(lo, 0) + 1))
    with cap(5, "is each query scanning all the values?"):
        got = count_in_ranges(values, queries)
    assert got == expected
