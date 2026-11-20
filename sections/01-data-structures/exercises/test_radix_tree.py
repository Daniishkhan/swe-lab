import random
import signal

import pytest

from radix_tree import RadixTree


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes about a second at most (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is an operation scanning every word or rebuilding the tree?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def check_shape(r, words):
    """The tree in r.structure() is compressed and spells exactly `words`."""
    spelled, nodes = [], 0

    def walk(node, path, is_root):
        nonlocal nodes
        nodes += 1
        assert isinstance(node, tuple) and len(node) == 2, f"node at {path!r} is not (is_word, children)"
        is_word, kids = node
        if is_word:
            spelled.append(path)
        firsts = [label[:1] for label in kids]
        assert all(firsts), f"empty edge label under {path!r}"
        assert len(set(firsts)) == len(firsts), f"two edges under {path!r} start with the same character: {sorted(kids)}"
        if not is_root:
            assert is_word or len(kids) >= 2, (
                f"node {path!r} is not a word and has {len(kids)} child(ren): it should be merged away")
        for label, child in kids.items():
            walk(child, path + label, False)

    walk(r.structure(), "", True)
    assert sorted(spelled) == sorted(words), "the paths don't spell the stored words"
    assert nodes == r.node_count(), f"structure() has {nodes} nodes but node_count() says {r.node_count()}"
    assert len(r) == len(words)


def leaf():
    return (True, {})


def test_example_splits():
    r = RadixTree()
    r.insert("test")
    assert r.structure() == (False, {"test": leaf()})
    r.insert("team")
    assert r.structure() == (False, {"te": (False, {"st": leaf(), "am": leaf()})})
    r.insert("tea")
    assert r.structure() == (False, {"te": (False, {"st": leaf(), "a": (True, {"m": leaf()})})})
    assert not r.contains("te") and r.contains("tea") and not r.contains("teams")
    assert r.starts_with("tes") and r.starts_with("te") and r.starts_with("")
    assert not r.starts_with("tex") and not r.starts_with("tests")
    r.insert("toast")
    r.insert("to")
    r.insert("ten")
    assert r.structure() == (False, {"t": (False, {
        "e": (False, {"st": leaf(), "a": (True, {"m": leaf()}), "n": leaf()}),
        "o": (True, {"ast": leaf()}),
    })})
    assert r.node_count() == 9 and len(r) == 6


def test_delete_merges():
    r = RadixTree()
    for w in ["test", "team", "tea", "toast", "to", "ten"]:
        r.insert(w)
    assert r.delete("to")  # "o" is no longer a word and has one child: merge into "oast"
    assert r.structure()[1]["t"][1]["o" + "ast"] == leaf()
    assert r.delete("tea")  # "a" merges with "m" into "am"
    assert r.delete("toast")  # "t" is left with one child: merge into "te"
    assert r.structure() == (False, {"te": (False, {"st": leaf(), "am": leaf(), "n": leaf()})})
    assert r.delete("toast") is False and r.delete("te") is False and r.delete("t") is False
    for w in ["test", "team", "ten"]:
        assert r.delete(w)
    assert r.structure() == (False, {}) and r.node_count() == 1 and len(r) == 0
    assert not r.starts_with("")


def test_prefix_of_an_edge_and_empty_word():
    r = RadixTree()
    r.insert("romane")
    r.insert("romanus")
    r.insert("roman")  # ends exactly at the split point
    assert r.structure() == (False, {"roman": (True, {"e": leaf(), "us": leaf()})})
    r.insert("rom")  # ends in the middle of an edge: split it
    assert r.structure() == (False, {"rom": (True, {"an": (True, {"e": leaf(), "us": leaf()})})})
    r.insert("")
    assert r.contains("") and r.structure()[0] is True and len(r) == 5
    r.insert("roman")
    assert len(r) == 5
    assert r.delete("") and not r.contains("")


def test_starts_with_inside_an_edge():
    r = RadixTree()
    r.insert("interview")
    for p in ["", "i", "int", "interv", "interview"]:
        assert r.starts_with(p), p
    for p in ["interviews", "x", "inx", "intervieW"]:
        assert not r.starts_with(p), p
    assert not r.contains("inter")


def test_random_against_a_set_with_shape_checks():
    rng = random.Random(31)
    for _ in range(40):
        r, ref = RadixTree(), set()
        for _ in range(120):
            w = "".join(rng.choice("ab") for _ in range(rng.randint(0, 5)))
            if rng.random() < 0.6:
                r.insert(w)
                ref.add(w)
            else:
                assert r.delete(w) == (w in ref), w
                ref.discard(w)
            assert r.contains(w) == (w in ref)
            p = "".join(rng.choice("ab") for _ in range(rng.randint(0, 3)))
            assert r.starts_with(p) == any(x.startswith(p) for x in ref), (p, sorted(ref))
            check_shape(r, ref)


def gen_words(n, seed):
    rng = random.Random(seed)
    syl = ["ca", "car", "co", "de", "do", "en", "er", "in", "ma", "mo", "ne", "on",
           "pa", "pre", "re", "sa", "st", "ta", "te", "to", "un", "x", "a", "e"]
    out = set()
    while len(out) < n:
        out.add("".join(rng.choice(syl) for _ in range(rng.randint(1, 6))))
    return sorted(out, key=lambda w: rng.random())


def plain_trie_nodes(words):
    return 1 + len({w[:i] for w in words for i in range(1, len(w) + 1)})


def test_big_and_compressed():
    words = gen_words(20_000, 8)
    r = RadixTree()
    for w in words:
        r.insert(w)
    check_shape(r, words)
    n, nodes, plain = len(words), r.node_count(), plain_trie_nodes(words)
    assert nodes <= 2 * n + 1, f"{nodes:,} nodes for {n:,} words: a radix tree needs at most 2n + 1"
    assert nodes < 0.6 * plain, f"{nodes:,} nodes vs {plain:,} for a plain trie: are chains being squeezed?"
    stored = set(words)
    rng = random.Random(9)
    for _ in range(50_000):
        w = rng.choice(words)
        q = w[: rng.randint(0, len(w))] + rng.choice(["", "", "a", "zz"])
        assert r.contains(q) == (q in stored), q
        assert r.starts_with(w[: rng.randint(0, len(w))])
    for w in words[: n // 2]:
        assert r.delete(w)
    check_shape(r, words[n // 2:])
