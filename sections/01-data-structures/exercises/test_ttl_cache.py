import random
import signal

import pytest

from ttl_cache import TTLCache


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something scanning every entry on each operation?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class T:
    """A time value that counts every comparison made with it (class-wide)."""

    __slots__ = ("v",)
    cmps = 0

    def __init__(self, v):
        self.v = float(v)

    @staticmethod
    def _v(o):
        return o.v if isinstance(o, T) else o

    def _c(self, o):
        T.cmps += 1
        return T._v(o)

    def __add__(self, o): return T(self.v + T._v(o))
    __radd__ = __add__
    def __sub__(self, o): return T(self.v - T._v(o))
    def __lt__(self, o): return self.v < self._c(o)
    def __le__(self, o): return self.v <= self._c(o)
    def __gt__(self, o): return self.v > self._c(o)
    def __ge__(self, o): return self.v >= self._c(o)
    def __eq__(self, o): return self.v == self._c(o)
    __hash__ = None
    def __float__(self): return self.v
    def __repr__(self): return f"T({self.v})"


class Clock:
    def __init__(self, start=0.0, counting=False):
        self.now, self.counting = start, counting

    def __call__(self):
        return T(self.now) if self.counting else self.now


class Model:
    """Slow, but simple enough to check by reading it."""

    def __init__(self, cap, ttl, clock):
        self.cap, self.ttl, self.clock = cap, ttl, clock
        self.order, self.d = [], {}  # order: least recent first; d: key -> [value, expires]

    def _purge(self):
        now = self.clock()
        dead = [k for k in self.order if self.d[k][1] <= now]
        for k in dead:
            self.order.remove(k)
            del self.d[k]
        return len(dead)

    def get(self, k, default=None):
        self._purge()
        if k not in self.d:
            return default
        self.order.remove(k)
        self.order.append(k)
        return self.d[k][0]

    def put(self, k, v):
        self._purge()
        if k in self.d:
            self.order.remove(k)
        self.order.append(k)
        self.d[k] = [v, self.clock() + self.ttl]
        if len(self.order) > self.cap:
            del self.d[self.order.pop(0)]


def test_example():
    now = [0.0]
    c = TTLCache(capacity=2, ttl=10, clock=lambda: now[0])
    c.put("a", 1)
    now[0] = 6
    c.put("b", 2)
    assert c.get("a") == 1
    now[0] = 10
    assert c.get("a") is None
    assert len(c) == 1 and "b" in c and "a" not in c


def test_invalid_arguments():
    for cap, ttl in [(0, 5), (-1, 5), (3, 0), (3, -2)]:
        with pytest.raises(ValueError):
            TTLCache(cap, ttl, clock=Clock())


def test_expires_exactly_at_ttl():
    clk = Clock()
    c = TTLCache(3, 5, clock=clk)
    c.put("a", 1)
    clk.now = 4.999
    assert c.get("a") == 1 and "a" in c and len(c) == 1
    clk.now = 5
    assert c.get("a", "gone") == "gone" and "a" not in c and len(c) == 0


def test_put_restarts_expiry_but_get_does_not():
    clk = Clock()
    c = TTLCache(3, 10, clock=clk)
    c.put("a", 1)
    c.put("b", 2)
    clk.now = 8
    c.put("a", 11)  # a now expires at 18
    c.get("b")  # b still expires at 10
    clk.now = 12
    assert c.get("a") == 11 and c.get("b") is None
    assert len(c) == 1


def test_lru_eviction_among_live_entries():
    clk = Clock()
    c = TTLCache(2, 100, clock=clk)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)  # all live: b is the least recently used
    assert "b" not in c and "a" in c and "c" in c and len(c) == 2


def test_expired_entries_go_before_live_ones():
    clk = Clock()
    c = TTLCache(3, 10, clock=clk)
    c.put("a", 1)  # expires at 10
    clk.now = 5
    c.put("b", 2)  # expires at 15
    c.put("c", 3)  # expires at 15
    c.get("a")  # a is now the MOST recent; b is the least recent
    clk.now = 11  # a has expired
    c.put("d", 4)  # 2 live entries + d = 3: nothing live may be evicted
    assert "b" in c and "c" in c and "d" in c and "a" not in c
    assert len(c) == 3
    c.put("e", 5)  # now full of live entries: b (least recent) goes
    assert "b" not in c and len(c) == 3


def test_purge_expired_counts():
    clk = Clock()
    c = TTLCache(10, 10, clock=clk)
    for i in range(6):
        clk.now = i
        c.put(i, i)
    clk.now = 12.5  # 0, 1 and 2 have expired (at 10, 11, 12)
    assert c.purge_expired() == 3
    assert c.purge_expired() == 0
    assert len(c) == 3 and all(i in c for i in (3, 4, 5))
    clk.now = 100
    assert c.purge_expired() == 3 and len(c) == 0
    c.put("x", 1)
    assert len(c) == 1 and c.get("x") == 1


def test_contains_does_not_touch_order():
    clk = Clock()
    c = TTLCache(2, 100, clock=clk)
    c.put("a", 1)
    c.put("b", 2)
    assert "a" in c
    c.put("c", 3)  # "a" was only checked, so it is still the least recent
    assert "a" not in c and "b" in c


def test_random_against_model():
    rng = random.Random(31)
    for _ in range(60):
        cap, ttl = rng.randint(1, 6), rng.choice([1, 3, 7])
        clk = Clock()
        c, m = TTLCache(cap, ttl, clock=clk), Model(cap, ttl, clk)
        for _ in range(250):
            clk.now += rng.choice([0, 0, 0.5, 1])
            k, r = rng.randint(0, 9), rng.random()
            if r < 0.4:
                assert c.get(k, -1) == m.get(k, -1)
            elif r < 0.85:
                v = rng.randint(0, 99)
                c.put(k, v)
                m.put(k, v)
            elif r < 0.95:
                m._purge()
                assert (k in c) == (k in m.d)
            else:
                m._purge()
                c.purge_expired()
            m._purge()
            assert len(c) == len(m.d)


def test_purge_cost_is_proportional_to_what_expired():
    n = 20_000
    clk = Clock(counting=True)
    c = TTLCache(n + 10, 1000, clock=clk)
    for i in range(n):
        clk.now = i * 0.01  # entry i expires at 1000 + i/100
        c.put(i, i)
    # read in a scrambled order, so recency order != expiry order
    order = list(range(n))
    random.Random(2).shuffle(order)
    for i in order[: n // 2]:
        c.get(i)
    for i in range(5):  # the first to expire are now the most recently used
        c.get(i)
    clk.now = 1000.045  # entries 0..4 have expired
    T.cmps = 0
    assert c.purge_expired() == 5
    assert len(c) == n - 5
    assert T.cmps <= 60, (
        f"{T.cmps:,} time comparisons to purge 5 expired entries out of {n:,} "
        "(budget 60): is something checking every entry's expiry?"
    )
    clk.now = 1000.095  # 5 more
    T.cmps = 0
    assert len(c) == n - 10
    assert T.cmps <= 60, f"{T.cmps:,} time comparisons for len() after 5 more expired (budget 60)"


def test_many_operations_quickly():
    rng = random.Random(17)
    clk = Clock()
    c = TTLCache(30_000, 50, clock=clk)
    for i in range(200_000):
        clk.now = i * 0.001
        k = rng.randrange(100_000)
        if i % 3 == 0:
            c.get(k)
        else:
            c.put(k, i)
        if i % 100 == 0:
            len(c)
    assert 0 < len(c) <= 30_000
