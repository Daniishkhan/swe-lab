# Tests for delta_debug.py: shrink(items, fails).
# Every call to fails stands for one run of a slow program, so the tests
# count them. 1-minimality is checked with calls that aren't counted.
import random
import signal

import pytest

from delta_debug import shrink


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes a second or two at most (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 30 s cap: does the loop stop when no single item can go?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Runs:
    """Wraps a test function and counts how often it is run."""

    def __init__(self, test):
        self.test = test
        self.calls = 0

    def __call__(self, sub):
        self.calls += 1
        return bool(self.test(list(sub)))


def needs(*culprits):
    """The bug shows up when every one of these values is present."""
    want = set(culprits)
    return lambda sub: want.issubset(sub)


def is_sublist(sub, items):
    """sub's items appear in items in the same order (a subsequence)."""
    rest = iter(items)
    return all(any(x == y for y in rest) for x in sub)


def check_one_minimal(result, items, test):
    assert isinstance(result, list), f"return a list, not {type(result).__name__}"
    assert is_sublist(result, items), "the result must be items you were given, kept in their original order"
    assert test(list(result)), f"{result!r} doesn't fail any more: the answer must still show the bug"
    for i in range(len(result)):
        smaller = result[:i] + result[i + 1:]
        assert not test(smaller), (
            f"not 1-minimal: {result!r} still fails without position {i} ({result[i]!r}). "
            "Keep going until no single item can be removed.")


def run(items, test, budget=None):
    runs = Runs(test)
    original = list(items)
    result = shrink(items, runs)
    assert items == original, "shrink changed the list it was given; work on a copy"
    check_one_minimal(result, original, test)
    if budget is not None:
        assert runs.calls <= budget, (
            f"{runs.calls} runs of the test for {len(original)} items; the budget is {budget}. "
            f"Removing one item at a time costs about {len(original)}. Cut out big chunks first, "
            "and only go smaller when no chunk of the current size can go (section 7).")
    return result, runs.calls


# ---------------------------------------------------------------- correctness


def test_example_from_the_docstring():
    result, _ = run(list(range(16)), needs(3, 12))
    assert result == [3, 12]


def test_one_item_that_fails():
    result, _ = run(["boom"], needs("boom"))
    assert result == ["boom"]


def test_both_items_needed():
    result, _ = run(["a", "b"], needs("a", "b"))
    assert result == ["a", "b"]


def test_when_neither_half_can_go_alone():
    # One culprit in each half: removing either half makes the bug vanish.
    # Stopping there returns all 8 items, which isn't 1-minimal.
    result, _ = run(list(range(8)), needs(1, 6))
    assert result == [1, 6]


def test_keeps_the_original_order():
    def a_then_b(sub):
        return "a" in sub and "b" in sub[sub.index("a") + 1:]

    result, _ = run(["b", "a", "c", "b"], a_then_b)
    assert result == ["a", "b"]


def test_repeated_values_are_removed_by_position():
    # The bug needs three copies of "x". Removing by value deletes every
    # copy at once, so it can never get down to exactly three.
    items = ["x", "a", "x", "b", "x", "c", "x", "d"]
    result, _ = run(items, lambda sub: sub.count("x") >= 3)
    assert result == ["x", "x", "x"]


def test_a_bug_that_is_not_monotone():
    # A parser that chokes on an unclosed quote: an odd number of " marks.
    # Removing a quote can make the bug vanish *or* come back, so check
    # every answer, not only the ones that look done.
    items = list('say "hi", then "bye" and "ok" "')
    assert items.count('"') % 2 == 1
    run(items, lambda sub: sub.count('"') % 2 == 1)


def test_noise_around_one_culprit():
    rng = random.Random(7)
    items = [rng.choice("abcdefgh") for _ in range(300)] + ["CRASH"] + [rng.choice("abcdefgh") for _ in range(300)]
    result, _ = run(items, needs("CRASH"))
    assert result == ["CRASH"]


# ---------------------------------------------------------------- cost

N = 4000


@pytest.mark.parametrize("culprit", [0, 1, 1999, 2000, 1234, 3999])
def test_one_culprit_in_4000_items(culprit):
    result, _ = run(list(range(N)), needs(culprit), budget=100)
    assert result == [culprit]


TWO = [(0, 3999), (1999, 2000), (0, 1), (3998, 3999), (10, 3500), (100, 200), (2600, 3999), (1000, 3000)]
TWO += [tuple(sorted(random.Random(seed).sample(range(N), 2))) for seed in range(6)]


@pytest.mark.parametrize("culprits", TWO)
def test_two_culprits_in_4000_items(culprits):
    result, _ = run(list(range(N)), needs(*culprits), budget=600)
    assert result == list(culprits)


THREE = [(0, 1999, 3999), (5, 6, 7), (100, 2100, 3900), (3000, 3001, 3999)]
THREE += [tuple(sorted(random.Random(100 + seed).sample(range(N), 3))) for seed in range(4)]


@pytest.mark.parametrize("culprits", THREE)
def test_three_culprits_in_4000_items(culprits):
    result, _ = run(list(range(N)), needs(*culprits), budget=1000)
    assert result == list(culprits)
