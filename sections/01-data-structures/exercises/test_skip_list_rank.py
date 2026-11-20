import math
import random
import signal

import pytest

from skip_list_rank import SortedSet


@pytest.fixture(autouse=True)
def time_limit(request):
    """Each test takes about a second at most when rank work uses spans (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is rank or by_rank walking level 0 to count?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(15 if request.node.name == "test_by_rank_and_ranges_use_spans" else 10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class S:
    """A score that counts every comparison made with it (class-wide)."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = v

    def _o(self, other):
        S.cmps += 1
        return other.v

    def __lt__(self, o): return self.v < self._o(o)
    def __le__(self, o): return self.v <= self._o(o)
    def __gt__(self, o): return self.v > self._o(o)
    def __ge__(self, o): return self.v >= self._o(o)
    def __eq__(self, o): return isinstance(o, S) and self.v == self._o(o)
    def __ne__(self, o): return not (isinstance(o, S) and self.v == self._o(o))
    __hash__ = None
    def __repr__(self): return f"S({self.v})"


def make(seed=1, **kw):
    return SortedSet(rng=random.Random(seed), **kw)


def test_example():
    z = make()
    assert z.add("ann", 30) is True
    assert z.add("bob", 10) and z.add("cat", 20) and z.add("dan", 20)
    assert [z.rank(m) for m in ["bob", "cat", "dan", "ann"]] == [0, 1, 2, 3]
    assert z.by_rank(0) == ("bob", 10)
    assert z.range_by_rank(1, 2) == [("cat", 20), ("dan", 20)]
    assert z.add("bob", 40) is False
    assert z.rank("bob") == 3 and z.score("bob") == 40
    assert z.remove("cat") is True and z.remove("cat") is False
    assert z.rank("dan") == 0
    assert z.rank("zed") is None and z.score("zed") is None
    assert len(z) == 3


def test_empty_and_edges():
    z = make()
    assert len(z) == 0 and z.rank("a") is None and z.score("a") is None
    assert z.range_by_rank(0, 10) == [] and z.remove("a") is False
    with pytest.raises(IndexError):
        z.by_rank(0)
    z.add("a", 1)
    assert z.add("a", 1) is False and len(z) == 1
    assert z.by_rank(0) == ("a", 1)
    with pytest.raises(IndexError):
        z.by_rank(1)
    with pytest.raises(IndexError):
        z.by_rank(-1)
    assert z.range_by_rank(0, 0) == [("a", 1)]
    assert z.range_by_rank(0, 99) == [("a", 1)]
    assert z.range_by_rank(1, 5) == [] and z.range_by_rank(3, 2) == []
    assert z.remove("a") is True and len(z) == 0 and z.range_by_rank(0, 0) == []
    z.add("b", 2)
    assert z.rank("b") == 0


def test_ties_order_by_member():
    z = make(3)
    names = ["kim", "ali", "zoe", "bea", "max", "eve"]
    for m in names:
        z.add(m, 7)
    assert [z.rank(m) for m in sorted(names)] == list(range(len(names)))
    assert [m for m, _ in z.range_by_rank(0, 99)] == sorted(names)


def test_matches_brute_force():
    rng = random.Random(5)
    z, ref = make(6), {}
    members = [f"m{i:03d}" for i in range(150)]

    def order():
        return sorted(ref.items(), key=lambda kv: (kv[1], kv[0]))

    for step in range(3000):
        m = rng.choice(members)
        if rng.random() < 0.65:
            s = rng.randint(0, 20)  # few distinct scores: many ties
            assert z.add(m, s) == (m not in ref)
            ref[m] = s
        else:
            assert z.remove(m) == (m in ref)
            ref.pop(m, None)
        assert len(z) == len(ref)
        o = order()
        q = rng.choice(members)
        want = next((i for i, (mm, _) in enumerate(o) if mm == q), None)
        assert z.rank(q) == want, (step, q)
        assert z.score(q) == ref.get(q)
        if o:
            r = rng.randrange(len(o))
            assert z.by_rank(r) == o[r], (step, r)
            a = rng.randrange(len(o))
            b = a + rng.randint(-2, 12)
            assert z.range_by_rank(a, b) == (o[a:b + 1] if b >= a else []), (step, a, b)
    assert z.range_by_rank(0, len(ref)) == order()


def test_score_is_a_dict_lookup():
    z = make(7)
    rng = random.Random(8)
    members = [f"p{i}" for i in range(2000)]
    for m in members:
        z.add(m, S(rng.randrange(10 ** 6)))
    S.cmps = 0
    for m in members:
        assert z.score(m) is not None
    assert S.cmps == 0, f"score() made {S.cmps:,} score comparisons: keep a dict from member to score"


def test_rank_costs_log_n():
    n = 4096
    rng = random.Random(9)
    z = make(10)
    scores = rng.sample(range(10 * n), n)
    members = [f"u{i}" for i in range(n)]
    for m, s in zip(members, scores):
        z.add(m, S(s))
    by_score = sorted(range(n), key=lambda i: scores[i])
    want = {members[i]: r for r, i in enumerate(by_score)}
    probe = rng.sample(members, 2000)
    S.cmps = 0
    for m in probe:
        assert z.rank(m) == want[m]
    per = S.cmps / len(probe)
    budget = 8 * math.log2(n) + 40
    assert per <= budget, f"{per:.0f} score comparisons per rank() (budget {budget:.0f}): are you walking level 0 and counting?"


def test_by_rank_and_ranges_use_spans():
    n = 50_000
    rng = random.Random(11)
    z = make(12)
    scores = [rng.randrange(10 ** 9) for _ in range(n)]
    for i, s in enumerate(scores):
        z.add(f"k{i}", s)
    o = sorted((s, f"k{i}") for i, s in enumerate(scores))
    for _ in range(50_000):
        r = rng.randrange(n)
        assert z.by_rank(r) == (o[r][1], o[r][0])
    for _ in range(2000):
        a = rng.randrange(n)
        got = z.range_by_rank(a, a + 9)
        assert got == [(m, s) for s, m in o[a:a + 10]]
    # rank() too: walking level 0 and matching the member by name makes no
    # score comparisons, so only the clock catches it (about 25,000 steps a call).
    pos = {m: r for r, (s, m) in enumerate(o)}
    for _ in range(20_000):
        m = f"k{rng.randrange(n)}"
        assert z.rank(m) == pos[m]
