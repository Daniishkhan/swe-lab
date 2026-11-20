import ast
import inspect
import random
import signal
import tracemalloc

import pytest

import kmp_search
from kmp_search import count_in_stream, failure_table, kmp_find_all


@pytest.fixture(autouse=True)
def time_limit():
    """Every test here takes a few seconds at most with O(n + m) work (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the time cap: is something re-checking the pattern from scratch at every position?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
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


class Text:
    """A read-only string that counts reads. forward_only=True: no going back, no slicing."""

    def __init__(self, s, budget=10**12, forward_only=False, name="text"):
        self._s, self.reads, self.budget = s, 0, budget
        self.forward_only, self.furthest, self.name = forward_only, -1, name

    def _tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooMuchWork(f"over {self.budget:,} reads of the {self.name}: something rereads the same characters")

    def __len__(self):
        return len(self._s)

    def __getitem__(self, i):
        if isinstance(i, slice):
            if self.forward_only:
                raise TypeError("no slicing the text here: read it one character at a time, front to back")
            out = self._s[i]
            self._tick(len(out))
            return out
        if i < 0:
            i += len(self._s)
        if not 0 <= i < len(self._s):
            raise IndexError(f"{self.name} index out of range")
        if self.forward_only:
            assert i >= self.furthest, (
                f"read text[{i}] after already reading text[{self.furthest}]: KMP never moves back in the text")
            self.furthest = i
        self._tick()
        return self._s[i]

    def __iter__(self):
        for k, ch in enumerate(self._s):
            if self.forward_only:
                assert k >= self.furthest, (
                    f"read text[{k}] after already reading text[{self.furthest}]: KMP never moves back in the text")
            self.furthest = max(self.furthest, k)
            self._tick()
            yield ch

    def __repr__(self):
        return f"Text(len={len(self._s)})"

    __str__ = __repr__


def brute_find(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]


def brute_failure(p):
    out = []
    for i in range(len(p)):
        s = p[:i + 1]
        out.append(max(k for k in range(len(s)) if s[:k] == s[len(s) - k:]))
    return out


LIBRARY_SEARCH = {"find", "rfind", "index", "rindex", "count", "startswith", "endswith", "split",
                  "partition", "replace", "join"}


def test_builds_it_yourself():
    tree = ast.parse(inspect.getsource(kmp_search))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            assert "re" not in names, "no regular expressions: build the search from s[i] reads"
        if isinstance(node, ast.Attribute):
            assert node.attr not in LIBRARY_SEARCH, f".{node.attr} is a library search or a copy; build it from s[i] reads"
        if isinstance(node, ast.Compare):
            assert not any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops), (
                "`x in s` on strings is Python's own C search; KMP doesn't need `in` at all")


# ---------------------------------------------------------------------------
# 1. failure_table
# ---------------------------------------------------------------------------
def test_failure_examples():
    assert failure_table(Text("ababaca")) == [0, 0, 1, 2, 3, 0, 1]
    assert failure_table(Text("aaaa")) == [0, 1, 2, 3]
    assert failure_table(Text("abcd")) == [0, 0, 0, 0]
    assert failure_table(Text("aabaaab")) == [0, 1, 0, 1, 2, 2, 3]
    assert failure_table(Text("x")) == [0]


def test_failure_against_definition():
    rng = random.Random(2)
    for _ in range(400):
        p = "".join(rng.choice("ab" if rng.random() < 0.7 else "abc") for _ in range(rng.randint(1, 18)))
        assert failure_table(Text(p)) == brute_failure(p), p


@pytest.mark.parametrize("shape", ["aaaa", "aaab", "abab", "random ab", "fibonacci"])
def test_failure_table_is_linear(shape):
    m = 20_000
    if shape == "aaaa":
        p = "a" * m
    elif shape == "aaab":
        p = "a" * (m - 1) + "b"
    elif shape == "abab":
        p = "ab" * (m // 2 - 1) + "abb"
    elif shape == "random ab":
        rng = random.Random(4)
        p = "".join(rng.choice("ab") for _ in range(m))
    else:  # Fibonacci words have many nested borders: the fall-back loop gets real use
        a, b = "a", "ab"
        while len(b) < m:
            a, b = b, b + a
        p = b[:m]
    m = len(p)
    t = Text(p, budget=8 * m + 10, name="pattern")
    fail = failure_table(t)
    assert len(fail) == m
    if shape == "aaaa":
        assert fail[-1] == m - 1 and fail[100] == 100
    elif shape == "aaab":
        assert fail[-1] == 0 and fail[-2] == m - 2
    elif shape == "abab":
        assert fail[-2] == m - 3 and fail[-1] == 0 and fail[-3] == m - 4
    for i in [1, 2, 3, 57, 999]:  # spot-check against the definition
        assert fail[i] == brute_failure(p[:i + 1])[-1]


# ---------------------------------------------------------------------------
# 2. kmp_find_all
# ---------------------------------------------------------------------------
def test_find_example():
    assert kmp_find_all(Text("abababa", forward_only=True), Text("aba")) == [0, 2, 4]


def test_find_edges():
    for text, pattern, want in [("a", "a", [0]), ("a", "b", []), ("ab", "abc", []), ("", "a", []),
                                ("aaaa", "aa", [0, 1, 2]), ("xyzxyz", "xyz", [0, 3]), ("abc", "c", [2]),
                                ("aabaaabaaab", "aaab", [3, 7]), ("ababcababcabc", "ababc", [0, 5])]:
        assert kmp_find_all(Text(text, forward_only=True), Text(pattern)) == want, (text, pattern)


def test_find_against_brute_force():
    rng = random.Random(9)
    for _ in range(500):
        text = "".join(rng.choice("ab") for _ in range(rng.randint(0, 60)))
        pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 6)))
        assert kmp_find_all(Text(text, forward_only=True), Text(pattern)) == brute_find(text, pattern), (text, pattern)


@pytest.mark.parametrize("shape", ["a...ab", "all match", "abab", "random ab", "fibonacci"])
def test_find_reads_text_forward_once(shape):
    n, m = 60_000, 2_000
    rng = random.Random(5)
    if shape == "a...ab":
        text, pattern = "a" * n, "a" * (m - 1) + "b"
        want = []
    elif shape == "all match":
        text, pattern = "a" * n, "a" * m
        want = list(range(n - m + 1))
    elif shape == "abab":
        text, pattern = "ab" * (n // 2), "ab" * (m // 2 - 1) + "abb"
        want = []
    elif shape == "random ab":
        text = "".join(rng.choice("ab") for _ in range(n))
        pattern = text[30_000:30_000 + m]
        want = None
    else:
        a, b = "a", "ab"
        while len(b) < n:
            a, b = b, b + a
        text, pattern = b[:n], b[:m]
        want = None
    t = Text(text, budget=3 * n + 10, forward_only=True)
    p = Text(pattern, budget=8 * m + 6 * n + 10, name="pattern")
    got = kmp_find_all(t, p)
    if want is None:
        want = brute_find(text, pattern)
        assert want, "the test expects at least one match here"
    assert got == want



# ---------------------------------------------------------------------------
# 3. count_in_stream
# ---------------------------------------------------------------------------
def chunked(s, rng, max_len=7):
    i = 0
    while i < len(s):
        k = rng.randint(0, max_len)
        yield s[i:i + k]
        i += k


def test_stream_example():
    assert count_in_stream(["ab", "aba", "", "ba"], "aba") == 3
    assert count_in_stream(iter([]), "a") == 0
    assert count_in_stream(["", ""], "a") == 0
    assert count_in_stream(["a", "a", "a"], "aa") == 2
    assert count_in_stream(["xyz"], "xyzw") == 0


def test_stream_against_brute_force():
    rng = random.Random(13)
    for _ in range(400):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 60)))
        pattern = "".join(rng.choice("ab") for _ in range(rng.randint(1, 6)))
        assert count_in_stream(chunked(s, rng), pattern) == len(brute_find(s, pattern)), (s, pattern)


def planted_stream(total, chunk, m, plants, rng):
    """Random-looking 'ab' text with `plants` copies of a pattern that starts with x and
    ends with y, so the copies are the only matches. Each copy straddles a chunk boundary.
    Chunks are made one at a time, so the test itself holds only one chunk."""
    pattern = "x" + "".join(rng.choice("ab") for _ in range(m - 2)) + "y"
    starts = [k * chunk - m // 2 for k in sorted(rng.sample(range(1, total // chunk), plants))]
    base = "".join(rng.choice("ab") for _ in range(chunk))

    def chunks():
        for pos in range(0, total, chunk):
            buf = list(base)
            for st in starts:
                for j in range(max(st, pos), min(st + m, pos + chunk)):
                    buf[j - pos] = pattern[j - st]
            yield "".join(buf)

    return chunks, pattern, len(starts)


def test_stream_uses_little_memory():
    rng = random.Random(21)
    total, chunk, m = 1_000_000, 4096, 1000
    chunks, pattern, want = planted_stream(total, chunk, m, 25, rng)
    tracemalloc.start()
    try:
        got = count_in_stream(chunks(), pattern)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert got == want
    assert peak < 300_000, f"peak extra memory was {peak:,} bytes for a {total:,}-character stream; keep only O(m) state"


@pytest.mark.parametrize("shape", ["a...ab", "aaaa"])
def test_stream_is_linear_on_aaaa(shape):
    total, chunk, m = 3_000_000, 8192, 3000
    pattern = "a" * (m - 1) + "b" if shape == "a...ab" else "a" * m
    want = 0 if shape == "a...ab" else total - m + 1
    full, rest = divmod(total, chunk)

    def stream():
        for _ in range(full):
            yield "a" * chunk
        yield "a" * rest

    assert count_in_stream(stream(), pattern) == want



def test_stream_is_not_brute_force_on_a_buffer():
    """Keeping the last m characters and comparing them at every position is O(m) memory
    but n * m time: about a minute here even at C speed. KMP: about a second."""
    total, chunk, m = 1_000_000, 8192, 300_000
    ch, other = "\U0001F600", "\U0001F601"
    pattern = ch * (m // 2) + other + ch * (m - m // 2 - 1)
    full, rest = divmod(total, chunk)

    def stream():
        for _ in range(full):
            yield ch * chunk
        yield ch * rest

    assert count_in_stream(stream(), pattern) == 0
