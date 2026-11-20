import ast
import inspect
import random
import signal

import pytest

import longest_dup_substring as mod
from longest_dup_substring import longest_dup_substring


@pytest.fixture(autouse=True)
def time_limit():
    """Every test here takes under half a second with O(n log n) work. Trying lengths
    1, 2, 3, ... takes 25 seconds or more on the big tests, even on a list of ord()
    values that the read count can't see (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 5-second cap: how many lengths are you trying, and what does each try cost?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------------------
# A string that counts every character read; slices are counted views
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
    """A read-only string. s[i], for-loops, and comparing or hashing a slice all count reads."""

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
        cost = min(k + 1, len(mine))
        self.tally.tick(cost if not isinstance(other, Text) else 2 * cost)
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


def run(s, budget=10**12):
    tally = Tally(budget)
    got = longest_dup_substring(Text(s, tally))
    if isinstance(got, Text):
        got = got._raw()
    assert isinstance(got, str), f"return a str or a slice of the input, not {type(got).__name__}"
    return got


def occurs_twice(s, sub):
    first = s.find(sub)
    return first >= 0 and s.find(sub, first + 1) >= 0


def brute_length(s):
    best = 0
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            k = 0
            while j + k < len(s) and s[i + k] == s[j + k]:
                k += 1
            best = max(best, k)
    return best


LIBRARY_SEARCH = {"find", "rfind", "index", "rindex", "count", "startswith", "endswith", "split",
                  "partition", "replace", "join"}


def test_builds_it_yourself():
    tree = ast.parse(inspect.getsource(mod))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            assert "re" not in names, "no regular expressions: build the search from s[i] reads"
        if isinstance(node, ast.Attribute):
            assert node.attr not in LIBRARY_SEARCH, f".{node.attr} is a library search or a copy; build it from s[i] reads"


def test_examples():
    assert run("banana") == "ana"
    assert run("abcd") == ""
    assert run("aaaaa") == "aaaa"
    assert run("abcXabcYabc") == "abc"


def test_smallest():
    assert run("") == ""
    assert run("a") == ""
    assert run("aa") == "a"
    assert run("ab") == ""
    assert run("abab") == "ab"


def test_against_brute_force():
    rng = random.Random(17)
    for _ in range(400):
        s = "".join(rng.choice("ab" if rng.random() < 0.6 else "abc") for _ in range(rng.randint(0, 30)))
        got = run(s)
        want = brute_length(s)
        assert len(got) == want, (s, got, want)
        if want:
            assert occurs_twice(s, got), (s, got)


def test_unicode():
    s = "café ✓ naïve café ✓ x"
    got = run(s)
    assert got == "café ✓ " and occurs_twice(s, got)


def planted(n, length, rng, alphabet="abcdefghijklmnopqrstuvwxyz"):
    """Random text with one substring of `length` copied to a second place.
    The characters around both copies differ, so the copy can't grow: the answer is exactly `length` long."""
    s = [rng.choice(alphabet) for _ in range(n)]
    a = rng.randrange(1, n // 2 - length - 1)
    b = rng.randrange(n // 2, n - length - 1)
    s[b:b + length] = s[a:a + length]
    s[b - 1] = "A" if s[a - 1] != "A" else "B"
    s[b + length] = "Z" if s[a + length] != "Z" else "Y"
    return "".join(s)


@pytest.mark.parametrize("length", [300, 9_000, 1])
def test_planted_repeat_with_a_read_budget(length):
    rng = random.Random(length)
    n = 20_000
    if length == 1:  # every character distinct except one pair
        chars = [chr(0x4E00 + k) for k in range(n)]
        chars[n - 1] = chars[n // 3]
        s = "".join(chars)
    else:
        s = planted(n, length, rng)
    got = run(s, budget=60 * n)
    assert len(got) == length and occurs_twice(s, got)


@pytest.mark.parametrize("shape", ["aaaa", "abab", "no repeat"])
def test_extreme_shapes_with_a_read_budget(shape):
    n = 20_000
    if shape == "aaaa":
        s, want = "a" * n, n - 1
    elif shape == "abab":
        s, want = "ab" * (n // 2), n - 2
    else:
        s, want = "".join(chr(0x4E00 + k) for k in range(n)), 0
    got = run(s, budget=60 * n)
    assert len(got) == want and (want == 0 or occurs_twice(s, got))
