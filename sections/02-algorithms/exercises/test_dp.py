import itertools
import math
import random

import pytest

from dp import best_knapsack, count_ways, diff_lines, longest_increasing_subsequence, min_cut_cost


# ---------------------------------------------------------------------------
# Work meter. The numbers and strings below count every time your code uses
# them. Past the budget they raise, so brute force fails fast instead of hanging.
# ---------------------------------------------------------------------------
class TooMuchWork(AssertionError):
    pass


class Meter:
    def __init__(self):
        self.n, self.budget, self.what = 0, None, ""

    def start(self, budget, what):
        self.n, self.budget, self.what = 0, budget, what

    def stop(self):
        self.budget = None
        return self.n

    def tick(self):
        if self.budget is None:
            return
        self.n += 1
        if self.n > self.budget:
            self.budget = None
            raise TooMuchWork(f"over {self.n - 1:,} {self.what}: too much work for the target complexity (brute force?)")


METER = Meter()


class CountedInt(int):
    """An int that counts every comparison and every + - * // % it takes part in."""

    def __lt__(self, o): METER.tick(); return int.__lt__(self, o)
    def __le__(self, o): METER.tick(); return int.__le__(self, o)
    def __gt__(self, o): METER.tick(); return int.__gt__(self, o)
    def __ge__(self, o): METER.tick(); return int.__ge__(self, o)
    def __eq__(self, o): METER.tick(); return int.__eq__(self, o)
    def __ne__(self, o): METER.tick(); return int.__ne__(self, o)
    def __add__(self, o): METER.tick(); return int.__add__(self, o)
    def __radd__(self, o): METER.tick(); return int.__radd__(self, o)
    def __sub__(self, o): METER.tick(); return int.__sub__(self, o)
    def __rsub__(self, o): METER.tick(); return int.__rsub__(self, o)
    def __mul__(self, o): METER.tick(); return int.__mul__(self, o)
    def __rmul__(self, o): METER.tick(); return int.__rmul__(self, o)
    def __floordiv__(self, o): METER.tick(); return int.__floordiv__(self, o)
    def __mod__(self, o): METER.tick(); return int.__mod__(self, o)
    __hash__ = int.__hash__


class CountedStr(str):
    """A line of text that counts every == and != it takes part in."""

    def __eq__(self, o): METER.tick(); return str.__eq__(self, o)
    def __ne__(self, o): METER.tick(); return str.__ne__(self, o)
    __hash__ = str.__hash__


def counted(nums):
    return [CountedInt(x) for x in nums]


def lcg(seed, count, mod):
    """Deterministic pseudo-random ints (no dependence on the random module's internals)."""
    out, x = [], seed
    for _ in range(count):
        x = (x * 1103515245 + 12345) % 2**31
        out.append(x % mod)
    return out


# ---------------------------------------------------------------------------
# 4. count_ways
# ---------------------------------------------------------------------------
def brute_ways(coins, amount):
    """Try every count of every coin. Exponential, fine for tiny inputs."""
    if not coins:
        return 1 if amount == 0 else 0
    first, rest = coins[0], coins[1:]
    return sum(brute_ways(rest, amount - k * first) for k in range(amount // first + 1))


@pytest.mark.parametrize("coins, amount, expected", [
    ([1, 2, 5], 5, 4),
    ([5, 1, 2], 5, 4),          # order of the coins list doesn't matter
    ([1, 2], 4, 3),             # 2+2, 2+1+1, 1+1+1+1 (not 5: 1+2+1 is the same way as 2+1+1)
    ([2], 3, 0),
    ([10], 10, 1),
    ([1], 0, 1),
    ([], 0, 1),
    ([], 7, 0),
    ([3, 5, 7], 1, 0),
    ([7], 6, 0),
])
def test_count_ways_examples(coins, amount, expected):
    assert count_ways(coins, amount) == expected


def test_count_ways_matches_brute_force():
    rnd = random.Random(41)
    for _ in range(200):
        coins = rnd.sample(range(1, 12), rnd.randint(0, 4))
        amount = rnd.randint(0, 30)
        assert count_ways(list(coins), amount) == brute_ways(coins, amount), (coins, amount)


def test_count_ways_does_dp_work():
    coins, amount = [1, 2, 5, 10, 20, 50, 100, 200], 500
    budget = 20 * len(coins) * (amount + 1)
    METER.start(budget, "uses of a coin value")
    got = count_ways(counted(coins), amount)
    used = METER.stop()
    assert got == 6295434, "wrong count for making 500 from [1, 2, 5, 10, 20, 50, 100, 200]"
    assert used <= budget


# ---------------------------------------------------------------------------
# 5. best_knapsack
# ---------------------------------------------------------------------------
def brute_knapsack(weights, values, capacity):
    best = 0
    for r in range(len(weights) + 1):
        for pick in itertools.combinations(range(len(weights)), r):
            if sum(weights[i] for i in pick) <= capacity:
                best = max(best, sum(values[i] for i in pick))
    return best


def check_choice(weights, values, capacity, result, expected_value):
    value, chosen = result
    chosen = [int(i) for i in chosen]
    assert int(value) == expected_value, f"best value should be {expected_value}, got {value}"
    assert chosen == sorted(set(chosen)), "return the indices sorted, each at most once"
    assert all(0 <= i < len(weights) for i in chosen), "index out of range"
    assert sum(int(weights[i]) for i in chosen) <= capacity, "the chosen items are over the capacity"
    assert sum(int(values[i]) for i in chosen) == expected_value, "the chosen items don't add up to the value you returned"


@pytest.mark.parametrize("weights, values, capacity, expected", [
    ([1, 3, 4, 5], [1, 4, 5, 7], 7, 9),
    ([1, 3, 4, 5], [1, 4, 5, 7], 0, 0),
    ([], [], 10, 0),
    ([5], [10], 4, 0),          # too heavy
    ([5], [10], 5, 10),         # exactly fits
    ([2, 2], [3, 3], 4, 6),     # identical items: both
    ([2, 2], [3, 3], 3, 3),     # identical items: only one fits
    ([1, 2, 3], [0, 0, 0], 6, 0),
    ([3, 4, 2], [4, 5, 3], 7, 9),
])
def test_best_knapsack_examples(weights, values, capacity, expected):
    check_choice(weights, values, capacity, best_knapsack(weights, values, capacity), expected)


def test_best_knapsack_prompt_choice():
    assert best_knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7) == (9, [1, 2])


def test_best_knapsack_matches_brute_force():
    rnd = random.Random(52)
    for _ in range(200):
        n = rnd.randint(0, 9)
        weights = [rnd.randint(1, 8) for _ in range(n)]
        values = [rnd.randint(0, 12) for _ in range(n)]
        capacity = rnd.randint(0, 25)
        got = best_knapsack(list(weights), list(values), capacity)
        check_choice(weights, values, capacity, got, brute_knapsack(weights, values, capacity))


def _knapsack_work(weights, values, capacity, expected):
    n = len(weights)
    budget = 10 * n * (capacity + 1)
    w, v = counted(weights), counted(values)
    METER.start(budget, "uses of a weight or value")
    got = best_knapsack(w, v, capacity)
    METER.stop()
    check_choice(weights, values, capacity, got, expected)


def test_best_knapsack_does_dp_work_subset_sum():
    # value == weight, and the capacity is the weight of a hidden subset, so the best value IS the capacity.
    weights = [1 + (i * 37 + 11) % 97 for i in range(40)]
    capacity = sum(weights[i] for i in range(0, 40, 3))
    _knapsack_work(weights, list(weights), capacity, capacity)


# Answers for the big inputs below, worked out once by two independent reference solutions.
EXPECTED_KNAPSACK_700 = 1188


def test_best_knapsack_does_dp_work():
    weights = [1 + (i * 37 + 11) % 97 for i in range(40)]
    values = [1 + (i * 53 + 7) % 89 for i in range(40)]
    _knapsack_work(weights, values, 700, EXPECTED_KNAPSACK_700)



# ---------------------------------------------------------------------------
# 6. longest_increasing_subsequence
# ---------------------------------------------------------------------------
def is_subsequence(sub, seq):
    it = iter(seq)
    return all(any(x == y for y in it) for x in sub)


def brute_lis_length(nums):
    for r in range(len(nums), 0, -1):
        for pick in itertools.combinations(nums, r):
            if all(a < b for a, b in zip(pick, pick[1:])):
                return r
    return 0


def check_lis(nums, out, expected_len):
    out = [int(x) for x in out]
    assert len(out) == expected_len, f"longest has length {expected_len}, you returned {len(out)}: {out[:20]}"
    assert all(a < b for a, b in zip(out, out[1:])), f"not strictly increasing: {out[:20]}"
    assert is_subsequence(out, [int(x) for x in nums]), "not a subsequence: the values must appear in this order in nums"


@pytest.mark.parametrize("nums, expected_len", [
    ([10, 9, 2, 5, 3, 7, 101, 18], 4),
    ([], 0),
    ([5], 1),
    ([7, 7, 7, 7], 1),          # strictly increasing: equal values don't count
    ([1, 2, 3], 3),
    ([3, 2, 1], 1),
    ([0, 1, 0, 3, 2, 3], 4),
    ([2, 5, 3, 7, 1], 3),       # the tails list ends as [1, 3, 7], which is not a subsequence
    ([1, 3, 3, 2, 4], 3),
    ([-2, -1, -5, 0, -3], 3),   # negatives
])
def test_lis_examples(nums, expected_len):
    check_lis(nums, longest_increasing_subsequence(list(nums)), expected_len)


def test_lis_matches_brute_force():
    rnd = random.Random(63)
    for _ in range(200):
        nums = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 12))]
        check_lis(nums, longest_increasing_subsequence(list(nums)), brute_lis_length(nums))


EXPECTED_LIS_4000 = 123  # worked out once by two independent reference solutions


def test_lis_is_n_log_n():
    n = 4000
    nums = lcg(7, n, 100_000)
    budget = int(4 * n * math.log2(n))
    METER.start(budget, "comparisons")
    out = longest_increasing_subsequence(counted(nums))
    METER.stop()
    check_lis(nums, out, EXPECTED_LIS_4000)



# ---------------------------------------------------------------------------
# 7. diff_lines
# ---------------------------------------------------------------------------
def brute_lcs_length(a, b):
    if len(a) > len(b):
        a, b = b, a
    for r in range(len(a), 0, -1):
        for pick in itertools.combinations(a, r):
            if is_subsequence(pick, b):
                return r
    return 0


def check_diff(old, new, ops, kept_expected):
    ops = [(str(op), str(line)) for op, line in ops]
    assert all(op in (" ", "-", "+") for op, _ in ops), "ops must be ' ', '-' or '+'"
    assert [line for op, line in ops if op != "+"] == [str(x) for x in old], "the ' ' and '-' lines must spell out old"
    assert [line for op, line in ops if op != "-"] == [str(x) for x in new], "the ' ' and '+' lines must spell out new"
    kept = sum(1 for op, _ in ops if op == " ")
    assert kept == kept_expected, f"you kept {kept} lines, but {kept_expected} can be kept: the diff isn't minimal"


@pytest.mark.parametrize("old, new, kept", [
    (["a", "b", "c"], ["a", "c", "d"], 2),
    ([], [], 0),
    ([], ["x", "y"], 0),
    (["x", "y"], [], 0),
    (["a", "b"], ["a", "b"], 2),
    (["a", "b"], ["c", "d"], 0),
    (["a", "a", "a"], ["a", "a"], 2),           # duplicates
    (["a", "b", "a", "b"], ["b", "a", "b", "a"], 3),
])
def test_diff_examples(old, new, kept):
    check_diff(old, new, diff_lines(list(old), list(new)), kept)


def test_diff_prompt_example():
    got = [(str(op), str(line)) for op, line in diff_lines(["a", "b", "c"], ["a", "c", "d"])]
    assert got == [(" ", "a"), ("-", "b"), (" ", "c"), ("+", "d")]


def test_diff_matches_brute_force():
    rnd = random.Random(74)
    for _ in range(200):
        old = [rnd.choice("abc") for _ in range(rnd.randint(0, 8))]
        new = [rnd.choice("abc") for _ in range(rnd.randint(0, 8))]
        check_diff(old, new, diff_lines(list(old), list(new)), brute_lcs_length(old, new))


def test_diff_is_n_times_m():
    # old: 250 lines from a few repeating texts. new: 25 of them deleted and 25 brand-new lines
    # inserted, so exactly 225 lines can be kept.
    n = 250
    texts = ["return x", "x += 1", "}", "", "print(x)"]
    old = [texts[v] for v in lcg(3, n, len(texts))]
    gone = set(sorted(set(lcg(5, 80, n)))[:25])
    new = []
    for i, line in enumerate(old):
        if i % 10 == 4:
            new.append(f"new line {i}")
        if i not in gone:
            new.append(line)
    assert len(gone) == 25 and len(new) == 250
    old_c = [CountedStr(x) for x in old]
    new_c = [CountedStr(x) for x in new]
    budget = 3 * (len(old) + 1) * (len(new) + 1)
    METER.start(budget, "line comparisons")
    ops = diff_lines(old_c, new_c)
    METER.stop()
    check_diff(old, new, ops, 225)


# ---------------------------------------------------------------------------
# 8. min_cut_cost
# ---------------------------------------------------------------------------
def brute_cut_cost(length, cuts):
    best = None
    for order in itertools.permutations(cuts):
        pieces, cost = [(0, length)], 0
        for c in order:
            k = next(i for i, (a, b) in enumerate(pieces) if a < c < b)
            a, b = pieces.pop(k)
            cost += b - a
            pieces += [(a, c), (c, b)]
        best = cost if best is None else min(best, cost)
    return best or 0


@pytest.mark.parametrize("length, cuts, expected", [
    (7, [1, 3, 4, 5], 16),
    (9, [5, 6, 1, 4, 2], 22),
    (10, [], 0),
    (10, [4], 10),
    (2, [1], 2),
    (10, [1, 9], 19),            # cuts right next to the ends
])
def test_min_cut_cost_examples(length, cuts, expected):
    before = list(cuts)
    assert min_cut_cost(length, cuts) == expected
    assert cuts == before, "don't change the input list"


def test_min_cut_cost_matches_brute_force():
    rnd = random.Random(85)
    for _ in range(150):
        length = rnd.randint(2, 30)
        cuts = rnd.sample(range(1, length), min(length - 1, rnd.randint(0, 6)))
        assert min_cut_cost(length, list(cuts)) == brute_cut_cost(length, cuts), (length, cuts)


EXPECTED_CUT_1000 = 5717  # worked out once by two independent reference solutions


def test_min_cut_cost_is_cubic():
    length = 1000
    cuts = sorted(set(1 + (i * 389 + 17) % 999 for i in range(60)))
    assert len(cuts) == 60
    cuts = cuts[1::2] + cuts[::2][::-1]          # not sorted
    m = len(cuts)
    budget = 4 * (m + 2) ** 3                     # about 950,000; plain recursion needs far more
    METER.start(budget, "uses of a cut position")
    got = min_cut_cost(CountedInt(length), counted(cuts))
    METER.stop()
    assert int(got) == EXPECTED_CUT_1000

