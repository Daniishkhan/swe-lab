import hashlib
import random

import pytest

from rendezvous_hash import RendezvousHash

KEYS = [f"user:{i}" for i in range(20000)]


def H(text):
    return int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "big")


class CountingHash:
    """Wraps a hash function and counts calls. With a budget, raises the moment it's exceeded."""

    def __init__(self, fn=H, budget=None):
        self.fn, self.calls, self.budget = fn, 0, budget

    def __call__(self, text):
        self.calls += 1
        if self.budget is not None and self.calls > self.budget:
            raise AssertionError(f"hash_fn called more than {self.budget} times in one lookup")
        return self.fn(text)


def make(names, hash_fn=H):
    rh = RendezvousHash(hash_fn)
    for n in names:
        rh.add_node(n)
    return rh


def brute_order(names, hash_fn, key):
    return [n for _, n in sorted(((hash_fn(f"{n}|{key}"), n) for n in names), reverse=True)]


# Toy scores, readable by eye: TOY[key][node]
TOY = {
    "k1": {"A": 30, "B": 90, "C": 60},
    "k2": {"A": 70, "B": 10, "C": 40},
    "k3": {"A": 50, "B": 50, "C": 20},   # a tie between A and B
}


def toy(label):
    node, key = label.split("|")
    return TOY[key][node]


def test_highest_score_wins_on_a_toy_hash():
    rh = make(["A", "B", "C"], toy)
    assert rh.get_node("k1") == "B"
    assert rh.get_node("k2") == "A"
    assert rh.get_nodes("k1", 3) == ["B", "C", "A"]
    assert rh.get_nodes("k2", 2) == ["A", "C"]


def test_ties_go_to_the_larger_name():
    rh = make(["A", "B", "C"], toy)
    assert rh.get_node("k3") == "B"
    assert rh.get_nodes("k3", 3) == ["B", "A", "C"]


def test_constructor_takes_nodes():
    rh = RendezvousHash(toy, nodes=["A", "C"])
    assert rh.get_node("k1") == "C"


def test_fewer_nodes_than_k():
    rh = make(["A", "C"], toy)
    assert rh.get_nodes("k1", 5) == ["C", "A"]


def test_empty_and_errors():
    rh = RendezvousHash(H)
    with pytest.raises(LookupError):
        rh.get_node("k")
    with pytest.raises(LookupError):
        rh.get_nodes("k", 2)
    rh.add_node("a")
    with pytest.raises(ValueError):
        rh.add_node("a")
    with pytest.raises(KeyError):
        rh.remove_node("b")
    rh.remove_node("a")
    with pytest.raises(LookupError):
        rh.get_node("k")


def test_matches_brute_force():
    rng = random.Random(15)
    for trial in range(8):
        names = list(dict.fromkeys(f"n{rng.randrange(10**6)}" for _ in range(rng.randint(1, 9))))
        rh = make(names)
        for k in rng.sample(KEYS, 200):
            order = brute_order(names, H, k)
            assert rh.get_node(k) == order[0], (trial, k)
            assert rh.get_nodes(k, 3) == order[:3], (trial, k)


def test_adding_a_node_only_takes_what_it_wins():
    names = [f"cache-{i}" for i in range(10)]
    rh = make(names)
    before = {k: rh.get_node(k) for k in KEYS}
    rh.add_node("cache-10")
    moved = [k for k in KEYS if rh.get_node(k) != before[k]]
    frac = len(moved) / len(KEYS)
    assert 0.06 < frac < 0.13, f"{frac:.1%} moved; expected about 1/11 = 9.1%"
    assert all(rh.get_node(k) == "cache-10" for k in moved)


def test_removed_keys_go_to_their_second_choice():
    names = [f"cache-{i}" for i in range(10)]
    rh = make(names)
    top2 = {k: rh.get_nodes(k, 2) for k in KEYS}
    rh.remove_node("cache-4")
    receivers = {}
    for k in KEYS:
        first, second = top2[k]
        now = rh.get_node(k)
        if first == "cache-4":
            assert now == second
            receivers[now] = receivers.get(now, 0) + 1
        else:
            assert now == first, "a key that wasn't on the removed node moved"
    assert len(receivers) == 9, "the dead node's keys should spread over every survivor"


def test_balanced_without_virtual_nodes():
    rh = make([f"cache-{i}" for i in range(10)])
    counts = {}
    for k in KEYS:
        n = rh.get_node(k)
        counts[n] = counts.get(n, 0) + 1
    mean = len(KEYS) / 10
    assert len(counts) == 10
    assert max(counts.values()) < 1.15 * mean and min(counts.values()) > 0.85 * mean, counts


def test_one_hash_per_node_per_lookup():
    counter = CountingHash()
    names = [f"node-{i}" for i in range(25)]
    rh = make(names, counter)
    assert counter.calls == 0, "add_node doesn't need to hash anything"
    for k in KEYS[:400]:
        for call in (lambda: rh.get_node(k), lambda: rh.get_nodes(k, 1), lambda: rh.get_nodes(k, 5), lambda: rh.get_nodes(k, 25)):
            counter.calls, counter.budget = 0, len(names)
            call()
    counter.calls, counter.budget = 0, 0
    rh.remove_node("node-3")
