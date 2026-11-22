# Tests for differential.py: find_counterexample(candidate, oracle, alphabet, max_len).
# The toy problem: the most common value in a list, ties going to the
# smallest value, None for an empty list. It's the k = 1 case of
# py_toolkit's top_k_frequent (week 1), and the chapter's top_k_oracle
# sorts by the same (-count, value) key, so the correct version below
# gives nothing new away.
# Expected counterexamples were worked out by hand; the budget comes from
# where each one sits in the order, by arithmetic.
import signal
from collections import Counter

import pytest

from differential import find_counterexample


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 30 s cap")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------- the toy problem


def oracle(xs):
    """Slow and obviously right: values smallest first; keep one only if it has strictly more copies."""
    best = None
    for v in sorted(set(xs)):
        if best is None or xs.count(v) > xs.count(best):
            best = v
    return best


def crashes_on_empty(xs):
    return Counter(xs).most_common(1)[0][0]              # IndexError on []


def first_seen_wins_ties(xs):
    if not xs:
        return None
    return Counter(xs).most_common(1)[0][0]              # ties: first seen, not smallest


def largest_wins_ties(xs):
    if not xs:
        return None
    counts = Counter(xs)
    return max(counts, key=lambda v: (counts[v], v))     # ties: largest, not smallest


def assumes_sorted_input(xs):
    """Counts runs of equal neighbors: only right when equal values sit together."""
    best, best_len, run_len = None, 0, 0
    for i, x in enumerate(xs):
        run_len = run_len + 1 if i and xs[i - 1] == x else 1
        if run_len > best_len or (run_len == best_len and x < best):
            best, best_len = x, run_len
    return best


def sorts_its_input(xs):
    xs.sort()                                            # right answer, but the caller's list changed
    return assumes_sorted_input(xs)


def raises_on_three(xs):
    if 3 in xs:
        raise ValueError("unexpected value 3")
    return oracle(xs)


def correct(xs):
    counts = Counter(xs)
    return min(counts, key=lambda v: (-counts[v], v)) if counts else None


# ---------------------------------------------------------------- helpers


class Counted:
    def __init__(self, f):
        self.f = f
        self.calls = 0

    def __call__(self, xs):
        self.calls += 1
        return self.f(xs)


def lists_up_to(a, length):
    """How many lists of length 0..length over an alphabet of size a."""
    return sum(a ** k for k in range(length + 1))


def position(x, alphabet):
    """1-based position of x in the order: shorter first, then position by position."""
    a = len(alphabet)
    rank = 0
    for item in x:
        rank = rank * a + alphabet.index(item)
    return lists_up_to(a, len(x) - 1) + rank + 1


def run(candidate, alphabet, max_len, want):
    cand, orac = Counted(candidate), Counted(oracle)
    got = find_counterexample(cand, orac, list(alphabet), max_len)
    if want is None:
        assert got is None, f"{candidate.__name__}: they agree on every list up to length {max_len}, but got {got!r}"
        tried = lists_up_to(len(alphabet), max_len)
    else:
        assert isinstance(got, list), f"{candidate.__name__}: return the counterexample as a list, not {type(got).__name__}"
        assert got == want, f"{candidate.__name__}: the first disagreement is {want!r}, got {got!r}"
        tried = position(want, list(alphabet))
    for f in (cand, orac):
        assert f.calls <= 3 * tried, (
            f"{candidate.__name__}: {f.calls} calls to {f.f.__name__}, for a counterexample at list {tried}. "
            "Stop at the first disagreement instead of trying everything first.")
    return got


# ---------------------------------------------------------------- tests


def test_a_crash_is_a_disagreement():
    run(crashes_on_empty, [1, 2, 3], 4, [])


def test_ties_going_to_the_first_seen_value():
    run(first_seen_wins_ties, [1, 2, 3], 6, [2, 1])


def test_ties_going_to_the_largest_value():
    run(largest_wins_ties, [1, 2, 3], 6, [1, 2])


def test_a_hidden_assumption_that_the_input_is_sorted():
    # It's right on every list of length 0, 1 and 2, so the first
    # disagreement is the 24th list tried.
    run(assumes_sorted_input, [1, 2, 3], 6, [2, 1, 2])


def test_changing_the_input_is_a_disagreement():
    # Its answers are all right. Only comparing the input before and after
    # the call shows the bug, and that needs a copy taken before the call.
    run(sorts_its_input, [1, 2, 3], 6, [2, 1])


def test_any_exception_counts():
    run(raises_on_three, [1, 2, 3], 6, [3])


def test_a_correct_candidate_has_no_counterexample():
    run(correct, [1, 2, 3], 6, None)
    run(correct, ["b", "a"], 7, None)


def test_max_len_too_small_to_reach_the_bug():
    run(assumes_sorted_input, [1, 2, 3], 2, None)
    run(sorts_its_input, [1, 2, 3], 1, None)


def test_max_len_zero_tries_only_the_empty_list():
    run(crashes_on_empty, [1, 2, 3], 0, [])
    run(first_seen_wins_ties, [1, 2, 3], 0, None)


def test_the_alphabet_order_decides_what_comes_first():
    run(first_seen_wins_ties, [3, 2, 1], 6, [3, 2])
    run(largest_wins_ties, [3, 2, 1], 6, [3, 2])
    run(assumes_sorted_input, [3, 2, 1], 6, [3, 2, 3])


def test_other_kinds_of_values():
    run(first_seen_wins_ties, ["b", "a"], 5, ["b", "a"])
    run(largest_wins_ties, ["b", "a"], 5, ["b", "a"])
    run(assumes_sorted_input, ["b", "a"], 5, ["b", "a", "b"])
