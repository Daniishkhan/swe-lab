from token_bucket import TokenBucket


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def test_starts_full_then_rejects():
    clock = FakeClock()
    b = TokenBucket(5, 1, clock=clock)
    assert all(b.allow() for _ in range(5))
    assert b.allow() is False


def test_refills_over_time():
    clock = FakeClock()
    b = TokenBucket(5, 1, clock=clock)
    for _ in range(5):
        b.allow()
    clock.advance(1)
    assert b.allow() is True
    assert b.allow() is False


def test_fractional_refill():
    clock = FakeClock()
    b = TokenBucket(1, 2, clock=clock)
    assert b.allow()
    clock.advance(0.25)
    assert b.allow() is False
    clock.advance(0.25)
    assert b.allow() is True


def test_never_exceeds_capacity():
    clock = FakeClock()
    b = TokenBucket(3, 10, clock=clock)
    clock.advance(1000)
    assert sum(b.allow() for _ in range(10)) == 3


def test_cost_and_rejection_spends_nothing():
    clock = FakeClock()
    b = TokenBucket(5, 1, clock=clock)
    assert b.allow(cost=4)
    assert b.allow(cost=2) is False
    assert b.allow(cost=1) is True
    assert b.allow(cost=10) is False
