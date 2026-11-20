import random
import signal
import tracemalloc
from collections import deque

import pytest

from gas_station import circuit_start, min_jumps


def _alarm(seconds, why):
    """Context-free helper: raise TimeoutError after `seconds` (Unix only)."""
    def boom(*_):
        raise TimeoutError(why)
    old = signal.signal(signal.SIGALRM, boom)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    return old


@pytest.fixture(autouse=True)
def time_limit():
    if not hasattr(signal, "SIGALRM"):
        yield
        return
    old = _alarm(10, "over 10 s: is something trying every start or every jump?")
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


class Tally:
    """Shared read counter. With a limit, it raises as soon as the limit is passed,
    so a slow solution fails fast instead of running for minutes."""

    def __init__(self, limit=None):
        self.reads = 0
        self.limit = limit

    def add(self, k):
        self.reads += k
        if self.limit is not None and self.reads > self.limit:
            raise AssertionError(f"over {self.limit:,} item reads: is something re-reading the list for every start?")


class CountingList:
    """A read-only list that counts every item read (indexing, slicing, iterating)."""

    def __init__(self, items, tally=None):
        self._items = list(items)
        self.tally = tally or Tally()

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        if isinstance(i, slice):
            part = self._items[i]
            self.tally.add(len(part))
            return CountingList(part, self.tally)
        self.tally.add(1)
        return self._items[i]

    def __iter__(self):
        for x in self._items:
            self.tally.add(1)
            yield x


# ---------------------------------------------------------------- brute force (small inputs only)
def bfs_jumps(nums):
    n = len(nums)
    dist = [0] + [-1] * (n - 1)
    q = deque([0])
    while q:
        i = q.popleft()
        for j in range(i + 1, min(n, i + nums[i] + 1)):
            if dist[j] < 0:
                dist[j] = dist[i] + 1
                q.append(j)
    return dist[-1]


def drives_loop(gas, cost, s):
    n, tank = len(gas), 0
    for k in range(n):
        i = (s + k) % n
        tank += gas[i] - cost[i]
        if tank < 0:
            return False
    return True


def check_start(gas, cost, got):
    if sum(gas) < sum(cost):
        assert got == -1, f"total gas {sum(gas)} < total cost {sum(cost)}: no start works, expected -1, got {got}"
    else:
        assert got != -1, f"total gas {sum(gas)} >= total cost {sum(cost)}, so some start works: {gas}, {cost}"
        assert isinstance(got, int) and 0 <= got < len(gas), f"bad index {got}"
        assert drives_loop(gas, cost, got), f"starting at {got} runs dry: gas={gas}, cost={cost}"


# ---------------------------------------------------------------- 1. min_jumps
def test_jumps_examples():
    assert min_jumps([2, 3, 1, 1, 4]) == 2
    assert min_jumps([2, 3, 0, 1, 4]) == 2
    assert min_jumps([3, 2, 1, 0, 4]) == -1
    assert min_jumps([7]) == 0
    assert min_jumps([0]) == 0
    assert min_jumps([0, 1]) == -1
    assert min_jumps([1, 1, 1, 1]) == 3
    assert min_jumps([5, 1, 1, 1, 1, 1]) == 1, "one jump of 5 lands exactly on the last index"


def test_jumps_greedy_traps():
    # jumping as far as possible each time is wrong: 0 -> 2 lands on a 1
    assert min_jumps([2, 4, 1, 1, 1, 1]) == 2   # 0 -> 1 -> 5
    assert min_jumps([1, 2, 0, 1]) == 2          # 0 -> 1 -> 3
    assert min_jumps([3, 0, 0, 0, 1]) == -1


def test_jumps_random_small():
    rng = random.Random(30)
    for _ in range(500):
        nums = [rng.randint(0, 4) for _ in range(rng.randint(1, 14))]
        assert min_jumps(nums) == bfs_jumps(nums), nums


def test_jumps_reads():
    rng = random.Random(31)
    n = 30_000
    nums = [rng.randint(1, 6) for _ in range(n)]
    cl = CountingList(nums, Tally(limit=3 * n))
    assert min_jumps(cl) == 7153  # computed offline by brute-force BFS
    assert cl.tally.reads <= 3 * n, f"{cl.tally.reads:,} reads for {n:,} items (budget {3 * n:,}): one pass"


def test_jumps_long_jumps_fast():
    n = 30_000
    nums = [10_000] * n
    cl = CountingList(nums, Tally(limit=3 * n))
    if hasattr(signal, "SIGALRM"):
        _alarm(2, "over 2 s on 30,000 long jumps: are you updating every index each jump can reach?")
    assert min_jumps(cl) == 3   # 0 -> 10,000 -> 20,000 -> 29,999 is in reach
    assert cl.tally.reads <= 3 * n


def test_jumps_memory():
    n = 200_000
    nums = [2] * n
    if hasattr(signal, "SIGALRM"):
        _alarm(3, "over 3 s on 200,000 stones: one pass is enough")
    tracemalloc.start()
    try:
        got = min_jumps(nums)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert got == n // 2   # jumps of 2 from stone 0 reach stone n - 1 in n / 2 jumps
    assert peak < 20_000, f"peak extra memory {peak:,} bytes: keep the round's bounds in variables, not a table or a queue"


def test_jumps_does_not_modify_input():
    nums = [2, 3, 1, 1, 4]
    min_jumps(nums)
    assert nums == [2, 3, 1, 1, 4]


# ---------------------------------------------------------------- 2. circuit_start
def test_circuit_examples():
    assert circuit_start([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert circuit_start([2, 3, 4], [3, 4, 3]) == -1
    assert circuit_start([5], [5]) == 0
    assert circuit_start([4], [5]) == -1
    assert circuit_start([0, 0, 0], [0, 0, 0]) in (0, 1, 2)


def test_circuit_start_after_the_deepest_dip():
    gas, cost = [3, 1, 1, 7, 2], [2, 2, 5, 1, 4]
    check_start(gas, cost, circuit_start(gas, cost))
    assert circuit_start(gas, cost) == 3


def test_circuit_random_small():
    rng = random.Random(40)
    for _ in range(600):
        n = rng.randint(1, 10)
        gas = [rng.randint(0, 6) for _ in range(n)]
        cost = [rng.randint(0, 6) for _ in range(n)]
        check_start(gas, cost, circuit_start(gas, cost))


def test_circuit_does_not_modify_input():
    gas, cost = [1, 2, 3, 4, 5], [3, 4, 5, 1, 2]
    circuit_start(gas, cost)
    assert gas == [1, 2, 3, 4, 5] and cost == [3, 4, 5, 1, 2]


def adversarial_loop(n, seed):
    """gas[i] - cost[i] is 0 almost everywhere. The only start is m, in the middle:
    there the difference is +1, and at m - 1 it is -1. Every 4th station a is a
    decoy: +1 at a and -1 at a + 1, which cancel. Starting anywhere but m drives
    on until m - 1 before failing, so "try every start" reads about n^2 / 2 items
    in whichever order it tries them: left to right, right to left, or best
    gas - cost first."""
    rng = random.Random(seed)
    m = 4 * (n // 8) + 3                  # m - 1 and m are never decoy stations
    cost = [rng.randint(2, 50) for _ in range(n)]
    gas = cost[:]
    for a in range(0, n - 1, 4):
        gas[a] += 1
        gas[a + 1] -= 1
    gas[m - 1] -= 1
    gas[m] += 1
    return gas, cost, m


def test_circuit_reads():
    n = 20_000
    gas, cost, m = adversarial_loop(n, seed=41)
    t = Tally(limit=4 * n)
    got = circuit_start(CountingList(gas, t), CountingList(cost, t))
    assert got == m
    assert t.reads <= 4 * n, f"{t.reads:,} reads for {n:,} stations (budget {4 * n:,}): one pass over the loop"


def test_circuit_reads_no_start():
    n = 20_000
    gas, cost, m = adversarial_loop(n, seed=42)
    gas[m] -= 1   # now the total is one liter short
    t = Tally(limit=4 * n)
    assert circuit_start(CountingList(gas, t), CountingList(cost, t)) == -1
    assert t.reads <= 4 * n


def test_circuit_memory():
    n = 200_000
    gas, cost, m = adversarial_loop(n, seed=43)
    if hasattr(signal, "SIGALRM"):
        _alarm(3, "over 3 s on 200,000 stations: one pass is enough")
    tracemalloc.start()
    try:
        got = circuit_start(gas, cost)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert got == m
    assert peak < 20_000, f"peak extra memory {peak:,} bytes: keep running totals in variables, not a list"
