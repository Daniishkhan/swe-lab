import ast
import inspect
import random
import signal

import pytest

import rabin_karp
from rabin_karp import MOD, SubstringHasher, find_all, window_hashes


@pytest.fixture(autouse=True)
def time_limit():
    """Every test here takes well under a second with O(n + m) work. Recomputing every
    window from scratch, even from a list of ord() values that the read count can't see,
    takes 15 seconds or more on the big tests (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 3-second cap: is something recomputing every window from scratch?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(3)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------------------
# A string that counts every character read
# ---------------------------------------------------------------------------
class TooMuchWork(AssertionError):
    pass


class Tally:
    def __init__(self, budget=10**12):
        self.reads, self.budget = 0, budget

    def tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooMuchWork(f"over {self.budget:,} character reads: something rereads the same characters")


class Text:
    """A read-only string. s[i], for-loops, and comparing or hashing a slice all count reads.

    Slices are views (free to make), and reading their characters is counted
    on the same tally, so slicing can't hide work.
    """

    def __init__(self, s, tally=None, start=0, stop=None):
        self._s, self.tally = s, tally or Tally()
        self._a, self._b = start, len(s) if stop is None else stop

    def __len__(self):
        return self._b - self._a

    def __getitem__(self, i):
        n = len(self)
        if isinstance(i, slice):
            a, b, step = i.indices(n)
            if step != 1:
                raise TypeError("only plain slices s[i:j] are supported")
            return Text(self._s, self.tally, self._a + a, self._a + max(a, b))
        if i < 0:
            i += n
        if not 0 <= i < n:
            raise IndexError("Text index out of range")
        self.tally.tick()
        return self._s[self._a + i]

    def __iter__(self):
        for k in range(self._a, self._b):
            self.tally.tick()
            yield self._s[k]

    def _raw(self):
        return self._s[self._a:self._b]

    def __eq__(self, other):
        if isinstance(other, Text):
            o = other._raw()
        elif isinstance(other, str):
            o = other
        else:
            return NotImplemented
        mine = self._raw()
        if len(mine) != len(o):
            return False
        k = 0
        while k < len(mine) and mine[k] == o[k]:
            k += 1
        self.tally.tick(min(k + 1, len(mine)))  # characters compared before the answer was known
        if isinstance(other, Text):
            other.tally.tick(min(k + 1, len(mine)))  # ...on both sides
        return k == len(mine)

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else not r

    def __hash__(self):
        self.tally.tick(len(self))
        return hash(self._raw())

    def __repr__(self):
        return f"Text(len={len(self)})"

    __str__ = __repr__


def T(s, budget=10**12):
    t = Tally(budget)
    return Text(s, t), t


def H(s, base, mod):
    """The hash from the docstring, straight from its definition."""
    m = len(s)
    return sum(ord(c) * pow(base, m - 1 - k, mod) for k, c in enumerate(s)) % mod


def brute_find(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]


# ---------------------------------------------------------------------------
# No library search
# ---------------------------------------------------------------------------
LIBRARY_SEARCH = {"find", "rfind", "index", "rindex", "count", "startswith", "endswith", "split",
                  "partition", "replace", "join"}


def test_builds_it_yourself():
    tree = ast.parse(inspect.getsource(rabin_karp))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            assert "re" not in names, "no regular expressions: build the search from s[i] reads"
        if isinstance(node, ast.Attribute):
            assert node.attr not in LIBRARY_SEARCH, f".{node.attr} is a library search or a copy; build it from s[i] reads"


# ---------------------------------------------------------------------------
# 1. window_hashes
# ---------------------------------------------------------------------------
def test_window_hashes_example():
    t, _ = T("abcd")
    assert window_hashes(t, 2, 100, 10**9) == [9798, 9899, 10000]


def test_window_hashes_edges():
    t, _ = T("abc")
    assert window_hashes(t, 3, 31, 1000003) == [H("abc", 31, 1000003)]
    t, _ = T("abc")
    assert window_hashes(t, 4, 31, 1000003) == []
    t, _ = T("")
    assert window_hashes(t, 1, 31, 1000003) == []
    t, _ = T("zz")
    assert window_hashes(t, 1, 31, 7) == [ord("z") % 7] * 2


def test_window_hashes_against_definition():
    rng = random.Random(1)
    for _ in range(300):
        s = "".join(rng.choice("abcé✓") for _ in range(rng.randint(0, 25)))
        m = rng.randint(1, 8)
        base, mod = rng.randint(2, 10**6), rng.choice([7, 101, 10**9 + 7, MOD])
        t, _ = T(s)
        assert window_hashes(t, m, base, mod) == [H(s[i:i + m], base, mod) for i in range(len(s) - m + 1)]


@pytest.mark.parametrize("m", [1, 50, 5000])
def test_window_hashes_reads_each_character_about_twice(m):
    rng = random.Random(m)
    s = "".join(rng.choice("ab") for _ in range(30_000))
    n = len(s)
    t, tally = T(s, budget=3 * n + 10)
    base = rng.randint(256, MOD - 1)
    got = window_hashes(t, m, base, MOD)
    assert len(got) == n - m + 1
    for i in [0, 1, 7, n // 2, n - m]:
        assert got[i] == H(s[i:i + m], base, MOD), f"window {i} has the wrong hash"


# ---------------------------------------------------------------------------
# 2. find_all
# ---------------------------------------------------------------------------
def test_find_all_example():
    t, _ = T("abababa")
    p, _ = T("aba")
    assert find_all(t, p) == [0, 2, 4]


def test_find_all_edges():
    for text, pattern, want in [("a", "a", [0]), ("a", "b", []), ("ab", "abc", []), ("", "a", []),
                                ("aaaa", "aa", [0, 1, 2]), ("xyzxyz", "xyz", [0, 3]), ("abc", "c", [2])]:
        assert find_all(Text(text), Text(pattern)) == want, (text, pattern)


@pytest.mark.parametrize("mod", [2, 7, 101, MOD])
def test_find_all_checks_every_hash_match(mod):
    """With mod 7, about 1 window in 7 has the pattern's hash by accident."""
    rng = random.Random(mod)
    for _ in range(300):
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 40)))
        pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 5)))
        base = rng.choice([None, 256, 257, 10**6 + 3]) if mod == MOD else rng.choice([256, 257, 10**6 + 3])
        assert find_all(Text(text), Text(pattern), base=base, mod=mod) == brute_find(text, pattern), (text, pattern, base, mod)


def test_find_all_unicode():
    assert find_all(Text("naïve café, café ✓"), Text("café")) == [6, 12]


@pytest.mark.parametrize("shape", ["a...ab", "random ab", "ab-repeat", "all match"])
def test_find_all_does_linear_work(shape):
    n, m = 40_000, 5_000
    rng = random.Random(7)
    if shape == "a...ab":  # the naive scan's worst case: n * m reads
        text, pattern, want = "a" * n, "a" * (m - 1) + "b", []
    elif shape == "random ab":
        text = "".join(rng.choice("ab") for _ in range(n))
        pattern = text[12_345:12_345 + m]
        want = brute_find(text, pattern)
    elif shape == "ab-repeat":
        text, pattern = "ab" * (n // 2), "ab" * (m // 2 - 1) + "ba"
        want = []
    else:  # every window matches; checking each match costs m, and that part is allowed
        n, m = 4_000, 200
        text, pattern, want = "a" * n, "a" * m, list(range(n - m + 1))
    occ = len(want)
    tally = Tally(budget=4 * (len(text) + m) + occ * 2 * (m + 1))  # checking a match reads both sides
    got = find_all(Text(text, tally), Text(pattern, tally))
    assert got == want



# ---------------------------------------------------------------------------
# 3. SubstringHasher
# ---------------------------------------------------------------------------
def test_substring_hasher_example():
    h = SubstringHasher(Text("abcabcx"))
    assert h.equal(0, 3, 3) is True
    assert h.equal(0, 3, 4) is False
    assert h.equal(1, 4, 2) is True
    assert h.equal(2, 2, 5) is True
    assert h.equal(5, 0, 0) is True


def test_substring_hasher_against_brute_force():
    rng = random.Random(3)
    for _ in range(60):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(1, 60)))
        h = SubstringHasher(Text(s), mod=rng.choice([MOD, 10**9 + 7]))
        for _ in range(200):
            length = rng.randint(0, len(s))
            i, j = rng.randint(0, len(s) - length), rng.randint(0, len(s) - length)
            assert h.equal(i, j, length) == (s[i:i + length] == s[j:j + length]), (s, i, j, length)


def test_substring_hasher_is_not_fooled_by_anagrams():
    s = "abba" + "baab" + "abab" + "baba"
    h = SubstringHasher(Text(s))
    assert h.equal(0, 4, 4) is False  # same letters, different order
    assert h.equal(8, 12, 4) is False
    assert h.equal(1, 4, 2) is False  # "bb" vs "ba"
    assert h.equal(0, 8, 2) is True   # "ab" == "ab"


def test_substring_hasher_reads_once_and_queries_read_nothing():
    rng = random.Random(11)
    n = 50_000
    s = "".join(rng.choice("abc") for _ in range(n))
    tally = Tally(budget=2 * n + 10)
    h = SubstringHasher(Text(s, tally))
    before = tally.reads
    copies = [(i, i + 30_000) for i in range(0, 20_000, 997)]
    for i, j in copies:
        assert h.equal(i, j, 15) == (s[i:i + 15] == s[j:j + 15])
    s2 = s[:25_000] + s[:25_000]  # second half is a copy of the first
    h2 = SubstringHasher(Text(s2))
    assert h2.equal(0, 25_000, 25_000) is True
    assert h2.equal(0, 25_001, 24_999) is (s2[0:24_999] == s2[25_001:])
    for _ in range(5_000):
        length = rng.randint(1, 1000)
        i, j = rng.randint(0, n - length), rng.randint(0, n - length)
        h.equal(i, j, length)
    assert tally.reads == before, f"equal() read {tally.reads - before:,} characters; it should only use the stored numbers"
