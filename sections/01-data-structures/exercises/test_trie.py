import random
import signal
import tracemalloc

import pytest

from trie import Trie


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes about a second at most when every operation walks one
    path (Unix only). Scanning all words, or walking a whole subtree per
    call, takes minutes."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is a call walking the whole subtree, or scanning every word?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


SYLLABLES = ["ca", "car", "co", "de", "do", "en", "er", "in", "ma", "mo", "ne", "on",
             "pa", "pre", "re", "sa", "st", "ta", "te", "to", "un", "x", "a", "e"]


def gen_words(n, seed):
    """n distinct pseudo-words made of syllables, so many share prefixes."""
    rng = random.Random(seed)
    out = set()
    while len(out) < n:
        out.add("".join(rng.choice(SYLLABLES) for _ in range(rng.randint(1, 5))))
    return sorted(out, key=lambda w: rng.random())  # a shuffled order to insert in


def make(words=("car", "card", "care", "cart", "cat", "do", "dog")):
    t = Trie()
    for w in words:
        t.insert(w)
    return t


def test_example():
    t = make()
    assert t.contains("car") and not t.contains("ca")
    assert t.starts_with("ca")
    assert t.count_prefix("car") == 4
    assert t.words_with_prefix("car") == ["car", "card", "care", "cart"]
    assert t.words_with_prefix("", limit=2) == ["car", "card"]
    assert t.delete("card") is True
    assert t.delete("card") is False
    assert len(t) == 6


def test_contains_is_exact():
    t = make()
    for w in ["car", "card", "care", "cart", "cat", "do", "dog"]:
        assert t.contains(w), w
    for w in ["c", "ca", "cards", "carts", "d", "dogs", "x", ""]:
        assert not t.contains(w), w


def test_starts_with():
    t = make()
    for p in ["", "c", "ca", "car", "card", "d", "do", "dog"]:
        assert t.starts_with(p), p
    for p in ["x", "cb", "cards", "dot", "e"]:
        assert not t.starts_with(p), p
    assert not Trie().starts_with("")
    assert not Trie().contains("")


def test_empty_string_is_a_word():
    t = Trie()
    t.insert("")
    assert t.contains("") and len(t) == 1 and t.count_prefix("") == 1
    t.insert("a")
    assert t.words_with_prefix("") == ["", "a"]
    assert t.delete("") and not t.contains("") and t.contains("a") and len(t) == 1


def test_duplicates_are_stored_once():
    t = make()
    t.insert("car")
    t.insert("car")
    assert len(t) == 7
    assert t.count_prefix("car") == 4
    assert t.count_prefix("") == 7
    assert t.words_with_prefix("ca", limit=2) == ["car", "card"]


def test_words_with_prefix_sorted_and_limited():
    t = make(["to", "tea", "ted", "ten", "i", "in", "inn", "A", "Ab"])
    assert t.words_with_prefix("") == ["A", "Ab", "i", "in", "inn", "tea", "ted", "ten", "to"]
    assert t.words_with_prefix("te") == ["tea", "ted", "ten"]
    assert t.words_with_prefix("te", limit=2) == ["tea", "ted"]
    assert t.words_with_prefix("te", limit=0) == []
    assert t.words_with_prefix("te", limit=10) == ["tea", "ted", "ten"]
    assert t.words_with_prefix("z") == []
    assert t.words_with_prefix("inn") == ["inn"]


def test_any_characters():
    t = make(["naïve", "naive", "日本", "日本語", "a b", "a-b"])
    assert t.contains("日本") and t.contains("naïve") and not t.contains("日")
    assert t.words_with_prefix("日") == ["日本", "日本語"]
    assert t.words_with_prefix("a") == ["a b", "a-b"]
    assert t.count_prefix("na") == 2


def test_delete_keeps_the_other_words():
    t = make()
    assert t.delete("car")  # "car" is a prefix of other words: they must survive
    assert not t.contains("car") and t.contains("card") and t.contains("cart")
    assert t.count_prefix("car") == 3 and len(t) == 6
    assert t.delete("dog")  # "do" is a prefix of "dog": it must survive
    assert t.contains("do") and not t.starts_with("dog")
    assert t.delete("ca") is False and t.delete("cards") is False and t.delete("zebra") is False
    assert len(t) == 5
    for w in ["card", "care", "cart", "cat", "do"]:
        assert t.delete(w)
    assert len(t) == 0 and not t.starts_with("") and t.words_with_prefix("") == []
    t.insert("cat")
    assert t.words_with_prefix("") == ["cat"] and t.count_prefix("c") == 1


def test_random_against_a_set():
    rng = random.Random(21)
    for _ in range(60):
        t, ref = Trie(), set()
        for _ in range(150):
            w = "".join(rng.choice("abc") for _ in range(rng.randint(0, 4)))
            op = rng.random()
            if op < 0.5:
                t.insert(w)
                ref.add(w)
            elif op < 0.75:
                assert t.delete(w) == (w in ref), w
                ref.discard(w)
            else:
                assert t.contains(w) == (w in ref), w
            p = "".join(rng.choice("abc") for _ in range(rng.randint(0, 2)))
            want = sorted(x for x in ref if x.startswith(p))
            assert t.count_prefix(p) == len(want), (p, sorted(ref))
            assert t.starts_with(p) == bool(want)
            k = rng.choice([None, 1, 2, 5])
            assert t.words_with_prefix(p, k) == (want if k is None else want[:k]), (p, k)
            assert len(t) == len(ref)


def test_count_prefix_reads_one_number():
    words = gen_words(40_000, 1)
    t = Trie()
    for w in words:
        t.insert(w)
    letters = sorted({w[0] for w in words})
    prefixes = letters + [w[:2] for w in words[:50]]
    want = {p: sum(1 for w in words if w.startswith(p)) for p in prefixes}
    rng = random.Random(2)
    for _ in range(300_000):  # walking the subtree to count costs thousands of nodes per call
        p = rng.choice(prefixes)
        assert t.count_prefix(p) == want[p], p


def test_limit_stops_early():
    words = gen_words(40_000, 3)
    t = Trie()
    for w in words:
        t.insert(w)
    first3 = sorted(words)[:3]
    for _ in range(5_000):  # collecting all 40,000 words and slicing visits ~106,000 nodes per call
        assert t.words_with_prefix("", limit=3) == first3
    c_words = sorted(w for w in words if w.startswith("c"))
    for _ in range(3_000):
        assert t.words_with_prefix("c", limit=2) == c_words[:2]


def test_many_lookups():
    words = gen_words(20_000, 4)
    t = Trie()
    for w in words:
        t.insert(w)
    stored = set(words)
    rng = random.Random(5)
    for _ in range(100_000):  # a list scan per call would be 20,000 checks: 2 billion per kind of call
        w = rng.choice(words)
        q = w + rng.choice(["", "", "x", "zz"])
        assert t.contains(q) == (q in stored)
        p = w[: rng.randint(0, len(w))]
        assert t.starts_with(p)
        assert not t.starts_with(p + "Q")


def test_delete_frees_memory():
    words = gen_words(5_000, 6)
    tracemalloc.start()
    try:
        t = Trie()
        base = tracemalloc.get_traced_memory()[0]
        for w in words:
            t.insert(w)
        full = tracemalloc.get_traced_memory()[0]
        for w in words:
            assert t.delete(w), w
        empty = tracemalloc.get_traced_memory()[0]
    finally:
        tracemalloc.stop()
    used, freed = full - base, full - empty
    assert len(t) == 0 and not t.starts_with("")
    assert freed >= 0.9 * used, (
        f"inserts took {used:,} bytes but deleting every word freed only {freed:,}: "
        "remove the nodes that no longer lead to any word")
