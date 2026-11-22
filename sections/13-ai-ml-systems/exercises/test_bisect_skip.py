# Tests for bisect_skip.py: first_bad(n, is_bad).
# Every call to is_bad stands for a build and a test run, so the tests count
# them. Expected answers come straight from the definition in the docstring.
import math
import signal

import pytest

from bisect_skip import first_bad


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes a second or two at most (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 30 s cap: does the loop stop once only untestable versions are left? "
                           "Or is each \"did I already ask?\" lookup a scan through a list?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Versions:
    """Versions 1..n. `first` is the first bad one; versions in `untestable` answer None."""

    def __init__(self, n, first, untestable=()):
        self.n, self.first = n, first
        self.untestable = set(untestable) - {n}
        self.calls = 0
        self.nones = 0
        self.asked = set()
        self.repeats = []

    def __call__(self, v):
        assert isinstance(v, int) and 1 <= v <= self.n, f"is_bad({v!r}): versions are numbered 1..{self.n}"
        self.calls += 1
        if v in self.asked:
            self.repeats.append(v)
        self.asked.add(v)
        if v in self.untestable:
            self.nones += 1
            return None
        return v >= self.first

    def expected(self):
        """Straight from the definition: walk out from the first bad version."""
        hi = self.first
        while hi in self.untestable:
            hi += 1
        lo = self.first
        while lo - 1 >= 1 and lo - 1 in self.untestable:
            lo -= 1
        return (lo, hi)

    def budget(self):
        return math.ceil(math.log2(self.n)) + 1 + 2 * self.nones


def run(n, first, untestable=(), check_budget=True):
    versions = Versions(n, first, untestable)
    got = first_bad(n, versions)
    want = versions.expected()
    where = f"n = {n}, first bad = {first}, {len(versions.untestable)} untestable"
    assert tuple(got) == want, f"{where}: got {got!r}, want {want!r}"
    assert not versions.repeats, f"{where}: asked about version {versions.repeats[0]} twice; remember the answers"
    if check_budget:
        assert versions.calls <= versions.budget(), (
            f"{where}: {versions.calls} calls; the budget is {versions.budget()} "
            f"(ceil(log2 n) + 1 = {math.ceil(math.log2(n)) + 1}, plus 2 for each of the {versions.nones} None answers). "
            "Halve the range between the last good and the first bad version each time.")
    return versions


# ---------------------------------------------------------------- correctness


def test_example_from_the_docstring():
    run(8, 6, {5})
    run(8, 6)


def test_one_version():
    run(1, 1)


def test_first_version_is_bad():
    run(100, 1)
    run(100, 1, {2, 3})          # (1, 1): version 1 is testable and bad


def test_untestable_version_right_before_the_first_bad_one():
    v = run(100, 50, {49})
    assert v.expected() == (49, 50)


def test_first_bad_version_is_untestable():
    v = run(100, 50, {50, 51})
    assert v.expected() == (50, 52)


def test_every_small_case():
    # Every n up to 10, every first bad version, every set of untestable
    # versions among 1..n-1. Over 9,000 cases.
    for n in range(1, 11):
        for first in range(1, n + 1):
            for mask in range(1 << (n - 1)):
                untestable = {v for v in range(1, n) if mask >> (v - 1) & 1}
                run(n, first, untestable)


# ---------------------------------------------------------------- cost

BIG = 1_000_000


@pytest.mark.parametrize("first", [1, 2, 3, 500_000, 500_001, 654_321, 999_999, BIG])
def test_a_million_versions_none_untestable(first):
    run(BIG, first)


@pytest.mark.parametrize("n", [2, 3, 7, 8, 9, 1000, 1023, 1024, 1025, 2 ** 20])
def test_every_size_none_untestable(n):
    for first in sorted({1, 2, n // 3 or 1, n // 2 or 1, n - 1 or 1, n}):
        run(n, first)


def test_a_block_right_before_the_first_bad_version():
    v = run(BIG, 700_000, range(699_970, 700_000))
    assert v.expected() == (699_970, 700_000)


def test_a_block_starting_at_the_first_bad_version():
    v = run(BIG, 400_000, range(400_000, 400_005))
    assert v.expected() == (400_000, 400_005)


def test_a_block_in_the_middle_far_from_the_answer():
    # 300 untestable versions around 32,768, where the first probe lands.
    run(2 ** 16, 12_345, range(32_618, 32_918))


def test_everything_before_the_first_bad_version_is_untestable():
    v = run(2000, 1200, range(1, 1200))
    assert v.expected() == (1, 1200)


def test_every_second_version_untestable():
    v = run(4096, 1001, range(2, 4096, 2))
    assert v.expected() == (1000, 1001)


def test_a_pair_of_untestable_versions_every_4096():
    # Versions 4096k and 4096k + 1 can't be tested. A binary search over
    # 1..2**20 probes 524,288 or 524,289 first, depending on where its range
    # starts and how it rounds, and both are in here. So it has to step
    # around an untestable version straight away.
    untestable = set(range(4096, 2 ** 20, 4096)) | set(range(4097, 2 ** 20, 4096))
    run(2 ** 20, 777_777, untestable)
