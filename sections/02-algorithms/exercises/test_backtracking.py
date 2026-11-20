import itertools
import random
import sys

import pytest

from backtracking import can_partition_k, combination_sum, unique_permutations, word_search


class TooMuchWork(AssertionError):
    pass


class Work:
    """Counts operations. Gives up past `budget`, so a slow search fails fast instead of hanging."""

    def __init__(self, budget=10**8, what="operations"):
        self.n = 0
        self.budget = budget
        self.what = what

    def tick(self, k=1):
        self.n += k
        if self.n > self.budget:
            raise TooMuchWork(f"over {self.budget:,} {self.what}: the search explores branches it could cut")


class Item:
    """A value that counts every comparison and hash. Equal values are equal Items."""

    def __init__(self, value, work):
        self.value, self.work = value, work

    def _v(self, other):
        self.work.tick()
        return other.value if isinstance(other, Item) else other

    def __eq__(self, o): return self.value == self._v(o)
    def __ne__(self, o): return self.value != self._v(o)
    def __lt__(self, o): return self.value < self._v(o)
    def __le__(self, o): return self.value <= self._v(o)
    def __gt__(self, o): return self.value > self._v(o)
    def __ge__(self, o): return self.value >= self._v(o)

    def __hash__(self):
        self.work.tick()
        return hash(self.value)

    def __repr__(self): return f"Item({self.value!r})"


class Num(int):
    """An int that counts every +, -, and comparison made with it."""

    def __new__(cls, value, work):
        obj = int.__new__(cls, value)
        obj.work = work
        return obj

    def _t(self): self.work.tick()
    def __add__(self, o): self._t(); return int.__add__(self, o)
    def __radd__(self, o): self._t(); return int.__radd__(self, o)
    def __sub__(self, o): self._t(); return int.__sub__(self, o)
    def __rsub__(self, o): self._t(); return int.__rsub__(self, o)
    def __lt__(self, o): self._t(); return int.__lt__(self, o)
    def __le__(self, o): self._t(); return int.__le__(self, o)
    def __gt__(self, o): self._t(); return int.__gt__(self, o)
    def __ge__(self, o): self._t(); return int.__ge__(self, o)
    def __eq__(self, o): self._t(); return int.__eq__(self, o)
    def __ne__(self, o): self._t(); return int.__ne__(self, o)
    __hash__ = int.__hash__


def counting_calls(work, fn, *args):
    """Run fn(*args), ticking `work` on every function call (Python or built-in) it makes.
    Building every ordering and removing repeats only at the end compares nothing
    while it builds, so without this it would run for many minutes, holding
    hundreds of millions of orderings in memory, before failing."""
    def profile(frame, event, arg):
        if event in ("call", "c_call"):
            work.tick()
    sys.setprofile(profile)
    try:
        return fn(*args)
    finally:
        sys.setprofile(None)


def plain(x):
    return x.value if isinstance(x, Item) else int(x) if isinstance(x, Num) else x


# 4. unique_permutations
def brute_perms(vals):
    return sorted(set(itertools.permutations(vals)))


def norm_perms(out):
    return sorted(tuple(plain(x) for x in p) for p in out)


@pytest.mark.parametrize("vals", [[1, 1, 2], [], [5], [1, 2, 3], [7, 7, 7, 7], [2, 1, 2, 1], [3, 0, 3]])
def test_unique_permutations_examples(vals):
    before = list(vals)
    got = norm_perms(unique_permutations(vals))
    assert got == brute_perms(vals), "every distinct ordering, each exactly once"
    assert vals == before, "don't change the input list"


def test_unique_permutations_match_brute_force():
    rnd = random.Random(41)
    for _ in range(150):
        vals = [rnd.randint(0, 3) for _ in range(rnd.randint(0, 6))]
        got = norm_perms(unique_permutations(vals))
        assert len(got) == len(set(got)), f"{vals}: the same ordering came out twice"
        assert got == brute_perms(vals), f"wrong orderings for {vals}"


def test_unique_permutations_never_builds_a_repeat():
    vals = [1] * 8 + [2] * 2 + [3] * 2
    random.Random(42).shuffle(vals)
    work = Work(300_000, "comparisons and hashes")
    calls = Work(2_000_000, "function calls")
    items = [Item(v, work) for v in vals]
    got = norm_perms(counting_calls(calls, unique_permutations, items))
    want = sorted(vals)
    assert all(sorted(p) == want for p in got), "every ordering must use each number exactly as often as the input does"
    assert len(set(got)) == len(got), "the same ordering came out twice"
    assert len(got) == 2970, f"{len(got)} orderings; there are 12! / (8! 2! 2!) = 2,970"


# 5. combination_sum
def brute_combination_sum(cands, target):
    out = []
    if not cands:
        return out
    for length in range(1, target // min(cands) + 1):
        for combo in itertools.combinations_with_replacement(sorted(cands), length):
            if sum(combo) == target:
                out.append(combo)
    return sorted(out)


def norm_combos(out):
    return sorted(tuple(sorted(plain(x) for x in c)) for c in out)


@pytest.mark.parametrize("cands, target, expected", [
    ([2, 3, 6, 7], 7, [(2, 2, 3), (7,)]),
    ([2, 3, 5], 8, [(2, 2, 2, 2), (2, 3, 3), (3, 5)]),
    ([7, 3, 2], 7, [(2, 2, 3), (7,)]),
    ([2], 1, []),
    ([1], 1, [(1,)]),
    ([], 5, []),
    ([4, 5], 3, []),
    ([3], 9, [(3, 3, 3)]),
])
def test_combination_sum_examples(cands, target, expected):
    before = list(cands)
    assert norm_combos(combination_sum(cands, target)) == expected
    assert cands == before, "don't change the input list"


def test_combination_sum_matches_brute_force():
    rnd = random.Random(51)
    for _ in range(150):
        cands = rnd.sample(range(1, 13), rnd.randint(1, 5))
        target = rnd.randint(1, 20)
        got = norm_combos(combination_sum(list(cands), target))
        assert len(got) == len(set(got)), f"{cands}, {target}: a combination came out twice (in two orders?)"
        assert got == brute_combination_sum(cands, target), f"wrong answer for {cands}, {target}"


def _counted(cands, budget, seed):
    work = Work(budget, "additions, subtractions and comparisons")
    shuffled = list(cands)
    random.Random(seed).shuffle(shuffled)
    return [Num(c, work) for c in shuffled], work


def test_combination_sum_builds_each_combination_once():
    # Building every ORDER and removing repeats costs over 250,000 operations here.
    cands, _ = _counted([2, 3, 5, 7], 20_000, 52)
    assert norm_combos(combination_sum(cands, 30)) == brute_combination_sum([2, 3, 5, 7], 30)


def test_combination_sum_stops_at_the_first_candidate_too_big():
    # 104 candidates, but most nodes have only a little target left, and from
    # there only 3, 5 and 7 can fit. Trying all the big ones at every node
    # anyway (and rejecting each) costs over 1.5 million operations.
    raw = [3, 5, 7] + list(range(100, 201))
    cands, _ = _counted(raw, 500_000, 53)
    got = norm_combos(combination_sum(cands, 200))
    allowed = set(raw)
    assert all(sum(c) == 200 and set(c) <= allowed for c in got), "every combination must add up to 200"
    assert len(set(got)) == len(got), "a combination came out twice"
    assert len(got) == 2202, f"{len(got)} combinations; there are 2,202"


# 6. word_search
class Row:
    """One row of the board. Counts every cell read, refuses negative indexes."""

    def __init__(self, cells, work):
        self._cells = list(cells)
        self._work = work

    def _check(self, c):
        if isinstance(c, int) and c < 0:
            raise IndexError(f"column {c}: check the column is inside the board before reading it")

    def __getitem__(self, c):
        if isinstance(c, slice):
            part = self._cells[c]
            self._work.tick(len(part))
            return part
        self._check(c)
        self._work.tick()
        return self._cells[c]

    def __setitem__(self, c, value):
        self._check(c)
        self._cells[c] = value

    def __len__(self): return len(self._cells)

    def count(self, ch):
        self._work.tick(len(self._cells))
        return self._cells.count(ch)

    def __iter__(self):
        for ch in self._cells:
            self._work.tick()
            yield ch

    def __repr__(self): return repr(self._cells)


class Board(list):
    def __getitem__(self, r):
        if isinstance(r, int) and r < 0:
            raise IndexError(f"row {r}: check the row is inside the board before reading it")
        return list.__getitem__(self, r)


def make_board(rows, work=None):
    work = work or Work(what="cell reads")
    return Board(Row(r, work) for r in rows), work


def snapshot(board):
    return [list(row._cells) for row in board]


def brute_word_search(rows, word):
    cells = [(r, c) for r in range(len(rows)) for c in range(len(rows[0]))]
    if len(word) > len(cells):
        return False
    for walk in itertools.permutations(cells, len(word)):
        if all(rows[r][c] == ch for (r, c), ch in zip(walk, word)) and all(
                abs(r1 - r2) + abs(c1 - c2) == 1 for (r1, c1), (r2, c2) in zip(walk, walk[1:])):
            return True
    return False


EXAMPLE = [list("ABCE"), list("SFCS"), list("ADEE")]


@pytest.mark.parametrize("rows, word, expected", [
    (EXAMPLE, "ABCCED", True),
    (EXAMPLE, "SEE", True),
    (EXAMPLE, "ABCB", False),
    (EXAMPLE, "ASADFBCCEESE", True),
    ([["a"]], "a", True),
    ([["a"]], "b", False),
    ([["a"]], "aa", False),
    ([["a", "b"]], "aba", False),
    ([["a", "b"], ["b", "a"]], "abab", True),
    ([list("aab"), list("aaa")], "baaaaa", True),
])
def test_word_search_examples(rows, word, expected):
    board, _ = make_board(rows)
    before = snapshot(board)
    assert word_search(board, word) is expected
    assert snapshot(board) == before, "the board must look the same when you return: un-mark what you marked"


def test_word_search_matches_brute_force_and_restores_board():
    rnd = random.Random(61)
    for _ in range(120):
        h, w = rnd.randint(1, 3), rnd.randint(1, 3)
        rows = [[rnd.choice("ab") for _ in range(w)] for _ in range(h)]
        word = "".join(rnd.choice("ab") for _ in range(rnd.randint(1, 5)))
        board, _ = make_board(rows)
        expected = brute_word_search(rows, word)
        assert word_search(board, word) is expected, f"{rows}, {word!r}: expected {expected}"
        assert snapshot(board) == rows, f"{rows}, {word!r}: the board changed"


def _walk(rows, rnd, length):
    """Spell a word that's really on the board by taking a random walk."""
    h, w = len(rows), len(rows[0])
    while True:
        r, c = rnd.randrange(h), rnd.randrange(w)
        seen, word = {(r, c)}, rows[r][c]
        for _ in range(length - 1):
            steps = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                     if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in seen]
            if not steps:
                break
            r, c = rnd.choice(steps)
            seen.add((r, c))
            word += rows[r][c]
        if len(word) == length:
            return word


def test_word_search_stops_a_walk_at_the_first_wrong_letter():
    # 30 words of length 10 on an 8 x 8 board: 10 taken from real walks on the board,
    # 20 random (3 of those happen to be on the board too). Building whole walks and
    # only then comparing them with the word reads the board over 12 million times.
    rnd = random.Random(62)
    rows = [[rnd.choice("ABCD") for _ in range(8)] for _ in range(8)]
    words = [_walk(rows, rnd, 10) for _ in range(10)] + ["".join(rnd.choice("ABCD") for _ in range(10)) for _ in range(20)]
    on_board = [True] * 10 + [i in (3, 4, 12) for i in range(20)]
    work = Work(100_000, "cell reads")
    for word, expected in zip(words, on_board):
        board, _ = make_board(rows, work)
        assert word_search(board, word) is expected, f"{word!r}: expected {expected}"
        assert snapshot(board) == rows, "the board changed"


def test_word_search_rules_out_a_hopeless_word_before_searching():
    # 24 As and one B, and the word needs two Bs. A search that just starts walking
    # through the As reads the board over 1.4 million times before giving up.
    rows = [["A"] * 5 for _ in range(5)]
    rows[4][4] = "B"
    board, _ = make_board(rows, Work(5_000, "cell reads"))
    assert word_search(board, "A" * 14 + "BB") is False
    assert snapshot(board) == rows


# 7. can_partition_k
def brute_partition(nums, k):
    for deal in itertools.product(range(k), repeat=len(nums)):
        sums = [0] * k
        for x, g in zip(nums, deal):
            sums[g] += x
        if len(set(sums)) == 1 and len(set(deal)) == k:
            return True
    return False


@pytest.mark.parametrize("nums, k, expected", [
    ([4, 3, 2, 3, 5, 2, 1], 4, True),
    ([1, 2, 3, 4], 3, False),
    ([7], 1, True),
    ([1, 2, 3], 1, True),
    ([2, 2, 2, 2], 4, True),
    ([2, 2, 2, 3], 4, False),
    ([1, 1, 1, 1, 2, 2, 2, 2], 4, True),
    ([10, 1, 1, 1, 1, 1, 1, 1, 1, 2], 2, True),
    ([3, 3, 3, 3, 4], 2, False),
    ([5, 1, 1, 1], 2, False),
])
def test_can_partition_k_examples(nums, k, expected):
    before = list(nums)
    assert can_partition_k(nums, k) is expected
    assert nums == before, "don't change the input list"


def test_can_partition_k_matches_brute_force():
    rnd = random.Random(71)
    for _ in range(200):
        n = rnd.randint(1, 7)
        nums = [rnd.randint(1, 6) for _ in range(n)]
        k = rnd.randint(1, min(4, n))
        assert can_partition_k(list(nums), k) is brute_partition(nums, k), f"wrong answer for {nums}, k={k}"


@pytest.mark.parametrize("nums, k", [
    ([33, 38, 15, 20, 23, 18, 10, 8, 18, 38, 33, 37, 25, 19, 31, 34], 5),
    ([38, 18, 29, 10, 19, 17, 29, 14, 39, 11, 38, 13, 29, 9, 14, 25], 4),
])
def test_can_partition_k_cuts_the_search(nums, k):
    # No answer exists. Dealing every number into every group is k^n deals
    # (over 4 billion for 16 numbers and 4 groups); even with the "too full" cut,
    # skipping the largest-first order or the mirror-image cut costs over 2.8 million
    # operations here.
    work = Work(1_000_000, "additions, subtractions and comparisons")
    assert can_partition_k([Num(x, work) for x in nums], k) is False


def test_can_partition_k_finds_an_answer_with_pruning():
    nums = [26, 20, 12, 19, 5, 14, 10, 17, 26, 28, 9, 15, 12, 21, 14, 12]
    work = Work(1_000_000, "additions, subtractions and comparisons")
    assert can_partition_k([Num(x, work) for x in nums], 4) is True
