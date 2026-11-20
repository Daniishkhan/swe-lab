import math
import random
import signal

import pytest

from fanout_latency import fanout_quantile, max_fanout, prob_any_slow


@pytest.fixture(autouse=True)
def time_limit():
    """Formulas and one sort finish in well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 3 s: is there a loop over n, or a simulation?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(3)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Samples:
    """A read-only sequence of latencies that counts every item it hands out.
    Slices are Samples too and share the same tally."""

    def __init__(self, values, tally=None):
        self._v = list(values)
        self.tally = tally if tally is not None else [0]

    @property
    def reads(self):
        return self.tally[0]

    def __len__(self):
        return len(self._v)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Samples(self._v[i], self.tally)
        self.tally[0] += 1
        return self._v[i]

    def __iter__(self):
        for x in self._v:
            self.tally[0] += 1
            yield x

    def __repr__(self):
        return f"Samples(<{len(self._v)} latencies>)"


def shuffled(values, seed):
    v = list(values)
    random.Random(seed).shuffle(v)
    return v


def rel_ok(got, want, rel=1e-6):
    return math.isclose(got, want, rel_tol=rel, abs_tol=0.0) or got == want


# ---------- prob_any_slow ----------

# Worked out offline with 60-digit decimals from the exact double inputs.
@pytest.mark.parametrize("p,n,want", [
    (0.01, 100, 6.33967658726770503e-1),
    (0.001, 100, 9.52078528862909599e-2),
    (0.05, 20, 6.41514077591457787e-1),
    (0.5, 3, 0.875),
    (1e-12, 1000, 9.99999999500499980e-10),
])
def test_prob_any_slow_known(p, n, want):
    got = prob_any_slow(p, n)
    assert rel_ok(got, want), f"p={p}, n={n}: got {got!r}, want {want!r}"


def test_prob_any_slow_edges():
    assert prob_any_slow(0.3, 0) == 0.0
    assert prob_any_slow(0.0, 50) == 0.0
    assert prob_any_slow(1.0, 5) == 1.0
    assert rel_ok(prob_any_slow(0.3, 1), 0.3)
    assert prob_any_slow(1e-4, 10**7) == pytest.approx(1.0, abs=1e-12)
    # 99.9% up per server, 100 servers: 9.5% chance at least one is down.
    assert abs(prob_any_slow(0.001, 100) - 0.0952) < 1e-4


def test_prob_any_slow_tiny_p_keeps_digits():
    # 1 - (1 - 1e-12)**1000 in plain floats is off by about 5e-5 (relative).
    got = prob_any_slow(1e-12, 1000)
    assert rel_ok(got, 9.99999999500499980e-10)
    got = prob_any_slow(1e-15, 7)
    assert rel_ok(got, 7e-15, rel=1e-9)


# ---------- max_fanout ----------

def test_max_fanout_examples():
    assert max_fanout(0.01, 0.5) == 68          # ln(0.5)/ln(0.99) = 68.97
    assert max_fanout(0.001, 0.99) == 4602      # 4602.87
    assert max_fanout(1e-6, 0.01) == 10050      # 10050.33
    assert max_fanout(0.3, 0.9) == 6            # 6.46
    assert max_fanout(0.01, 0.005) == 0         # even one backend is too risky
    assert max_fanout(0.01, 0.0) == 0


def test_max_fanout_exact_boundaries():
    # With p = 0.5 every (1 - p)^n is exact in binary.
    assert max_fanout(0.5, 0.75) == 2           # 1 - 0.25 = 0.75 exactly: n = 2 is allowed
    assert max_fanout(0.5, 0.875) == 3
    assert max_fanout(0.5, 0.874) == 2
    assert max_fanout(0.5, 0.5) == 1


def test_max_fanout_huge_answers_need_a_formula():
    assert max_fanout(1e-9, 0.5) == 693_147_180          # 693,147,180.21
    assert max_fanout(1e-12, 0.1) == 105_360_515_657     # 105,360,515,657.77


def test_max_fanout_errors():
    for p, mx in [(0, 0.5), (1, 0.5), (-0.1, 0.5), (0.1, 1.0), (0.1, -0.1), (0.1, 2)]:
        with pytest.raises(ValueError):
            max_fanout(p, mx)


# ---------- fanout_quantile ----------

def near(got, want, step=1):
    return abs(got - want) <= step


def test_quantile_one_backend_is_plain_nearest_rank():
    s = Samples(shuffled(range(1, 100_001), 1))
    assert near(fanout_quantile(s, 1, 0.99), 99_000)   # 0.99 * 100,000 may land a hair off 99,000
    assert fanout_quantile(s, 1, 0.5) == 50_000       # 0.5 * 100,000 is exact
    assert fanout_quantile(s, 1, 1.0) == 100_000
    s = Samples([30, 10, 20, 50, 40, 100, 90, 60, 80, 70])
    assert fanout_quantile(s, 1, 0.5) == 50
    assert fanout_quantile(s, 1, 0.05) == 10
    # Two backends, median request: 0.5 ** (1/2) * 10 = 7.07, so rank 8 (round or floor say 7).
    assert fanout_quantile(s, 2, 0.5) == 80
    # 0.9 ** (1/3) * 10 = 9.65: rank 10.
    assert fanout_quantile(s, 3, 0.9) == 100
    # 0.3 ** (1/2) * 10 = 5.48: rank 6.
    assert fanout_quantile(s, 2, 0.3) == 60


def test_quantile_fanout_100_is_backend_p9999():
    s = Samples(shuffled(range(1, 100_001), 2))
    # level = 0.99 ** (1/100) = 0.9998995; rank = ceil(99,989.95) = 99,990
    assert fanout_quantile(s, 100, 0.99) == 99_990    # not a whole number: no slack
    s = Samples(shuffled(range(1, 1001), 3))
    # 0.5 ** (1/10) = 0.93303; rank 934
    assert fanout_quantile(s, 10, 0.5) == 934


def test_quantile_slow_tail_takes_over_the_median():
    # 99% of calls take 10 ms, 1% take 1000 ms.
    s = Samples(shuffled([10] * 9_900 + [1000] * 100, 4))
    assert fanout_quantile(s, 1, 0.5) == 10
    assert fanout_quantile(s, 1, 0.98) == 10
    assert fanout_quantile(s, 1, 0.995) == 1000
    assert fanout_quantile(s, 5, 0.5) == 10
    assert fanout_quantile(s, 68, 0.5) == 10      # rank 9,899 of 10,000: still fast
    assert fanout_quantile(s, 70, 0.5) == 1000    # rank 9,902: the median request is slow
    assert fanout_quantile(s, 100, 0.5) == 1000
    assert fanout_quantile(s, 100, 0.25) == 10    # rank 9,863


def test_quantile_reads_each_sample_a_few_times():
    values = shuffled(range(1, 200_001), 5)
    s = Samples(values)
    got = fanout_quantile(s, 1000, 0.99)
    # 0.99 ** (1/1000) * 200,000 = 199,997.99
    assert got == 199_998
    n = len(values)
    assert s.reads <= 3 * n + 100, f"{s.reads} reads of {n} samples: sort once, then pick one rank"
    assert s._v == values, "don't modify samples"


def test_quantile_budget_on_small_input_too():
    values = shuffled(range(1, 2001), 6)
    s = Samples(values)
    fanout_quantile(s, 20, 0.9)
    assert s.reads <= 3 * 2000 + 100


def test_quantile_errors():
    with pytest.raises(ValueError):
        fanout_quantile(Samples([]), 3, 0.5)
    for n in [0, -1]:
        with pytest.raises(ValueError):
            fanout_quantile(Samples([1, 2, 3]), n, 0.5)
    for q in [0, -0.5, 1.5]:
        with pytest.raises(ValueError):
            fanout_quantile(Samples([1, 2, 3]), 2, q)
