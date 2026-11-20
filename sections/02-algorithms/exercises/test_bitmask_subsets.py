import ast
import inspect
import math
import random
import signal

import pytest

import bitmask_subsets
from bitmask_subsets import masks_with_k_bits, submasks, subsets


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second when work grows with the answers (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: are you looping over every number up to the mask (or up to 2**n)? "
                           "Work must grow with the number of answers, not with the size of the mask.")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def test_no_itertools():
    tree = ast.parse(inspect.getsource(bitmask_subsets))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        assert not any(n.split(".")[0] == "itertools" for n in names), \
            f"line {node.lineno}: don't import itertools here: drive the bits yourself"


# ---------- 7a. subsets ----------

def test_subsets_example():
    assert subsets(["a", "b", "c"]) == [
        [], ["a"], ["b"], ["a", "b"], ["c"], ["a", "c"], ["b", "c"], ["a", "b", "c"]]


def test_subsets_empty_and_one():
    assert subsets([]) == [[]]
    assert subsets([42]) == [[], [42]]


def test_subsets_mask_order_and_input_untouched():
    items = [f"x{i}" for i in range(12)]
    before = list(items)
    out = subsets(items)
    assert items == before, "don't change the input list"
    assert len(out) == 2 ** 12
    for mask in (0, 1, 5, 6, 1000, 2730, 4095):
        want_members = {items[i] for i in range(12) if mask & (1 << i)}
        assert set(out[mask]) == want_members, f"result[{mask}] should hold the items whose bits are set in {mask:012b}"
        assert out[mask] == sorted(out[mask], key=items.index), f"result[{mask}]: keep the items in input order"


def test_subsets_with_duplicate_values():
    # Positions are what count, not values: two equal items still give 4 subsets.
    assert subsets([7, 7]) == [[], [7], [7], [7, 7]]


# ---------- 7b. submasks ----------

def brute_submasks(mask):
    return [s for s in range(mask, -1, -1) if s & ~mask == 0]


def test_submasks_example():
    assert submasks(0b1010) == [10, 8, 2, 0]
    assert submasks(0) == [0]
    assert submasks(1) == [1, 0]
    assert submasks(0b111) == [7, 6, 5, 4, 3, 2, 1, 0]


def test_submasks_match_brute_force():
    rng = random.Random(8)
    for _ in range(300):
        mask = rng.getrandbits(rng.randint(1, 12))
        assert submasks(mask) == brute_submasks(mask), f"submasks({mask:b})"


def test_submasks_of_a_wide_sparse_mask():
    mask = (1 << 50) | (1 << 25) | 1
    got = submasks(mask)
    assert got == [mask, (1 << 50) | (1 << 25), (1 << 50) | 1, 1 << 50, (1 << 25) | 1, 1 << 25, 1, 0]


def test_submasks_count_is_two_to_the_k():
    mask = sum(1 << p for p in range(0, 60, 4))  # 15 bits spread over 60 positions
    got = submasks(mask)
    assert len(got) == 2 ** 15
    assert got == sorted(got, reverse=True) and len(set(got)) == len(got)
    assert all(s & ~mask == 0 for s in got)


# ---------- 7c. masks_with_k_bits ----------

def brute_k_masks(n, k):
    return [m for m in range(1 << n) if sum((m >> i) & 1 for i in range(n)) == k]


def test_masks_with_k_bits_examples():
    assert masks_with_k_bits(4, 2) == [3, 5, 6, 9, 10, 12]
    assert masks_with_k_bits(5, 0) == [0]
    assert masks_with_k_bits(3, 3) == [7]
    assert masks_with_k_bits(0, 0) == [0]
    assert masks_with_k_bits(4, 1) == [1, 2, 4, 8]


def test_masks_with_k_bits_match_brute_force():
    for n in range(0, 11):
        for k in range(0, n + 1):
            assert masks_with_k_bits(n, k) == brute_k_masks(n, k), f"n={n}, k={k}"


def test_masks_with_k_bits_wide():
    got = masks_with_k_bits(60, 2)
    assert len(got) == math.comb(60, 2) == 1770
    assert got[:4] == [3, 5, 6, 9]
    assert got[-1] == (1 << 59) | (1 << 58)
    assert got == sorted(got) and len(set(got)) == len(got)
    assert all(m >> 60 == 0 and bin(m).count("1") == 2 for m in got)


def test_masks_with_k_bits_wide_and_many():
    got = masks_with_k_bits(40, 3)
    assert len(got) == math.comb(40, 3) == 9880
    assert got == sorted(got) and len(set(got)) == len(got)
    assert all(m >> 40 == 0 and bin(m).count("1") == 3 for m in got)
