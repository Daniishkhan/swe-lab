import random
import signal
import threading

import pytest

from striped_hash_map import StripedHashMap


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes about a second at most. A deadlock hangs forever, so
    stop after 20 s (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 20 s: a deadlock? Check the order in which transfer takes its locks.")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class Tracker:
    """Records what the map's locks do. For single-threaded tests: instead of
    hanging, a lock raises at once if taking it would risk a deadlock."""

    def __init__(self):
        self.made = []       # locks in creation order
        self.held = []       # stripe numbers held right now
        self.acquired = []   # every acquire, in order
        self.most_held = 0

    def factory(self):
        lock = TrackedLock(self, len(self.made))
        self.made.append(lock)
        return lock

    def reset(self):
        self.acquired.clear()
        self.most_held = 0


class TrackedLock:
    def __init__(self, tracker, stripe):
        self.t, self.stripe = tracker, stripe

    def acquire(self, blocking=True, timeout=-1):
        t = self.t
        if self.stripe in t.held:
            raise RuntimeError(f"stripe {self.stripe}'s lock taken while already held: threading.Lock would hang here forever")
        if t.held and max(t.held) > self.stripe:
            raise RuntimeError(f"took stripe {self.stripe} while holding stripe {max(t.held)}: "
                               "always take locks in increasing stripe order, or two threads can deadlock")
        t.held.append(self.stripe)
        t.acquired.append(self.stripe)
        t.most_held = max(t.most_held, len(t.held))
        return True

    def release(self):
        if self.stripe not in self.t.held:
            raise RuntimeError(f"released stripe {self.stripe}, which isn't held")
        self.t.held.remove(self.stripe)

    def locked(self):
        return self.stripe in self.t.held

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False


def tracked(num_stripes=16):
    t = Tracker()
    m = StripedHashMap(num_stripes, lock_factory=t.factory)
    assert len(t.made) == num_stripes, f"make one lock per stripe with lock_factory() (made {len(t.made)})"
    assert list(m.locks) == t.made, "self.locks[i] must be the i-th lock made"
    t.reset()
    return m, t


# ---- Behavior -------------------------------------------------------------
def test_example():
    m = StripedHashMap(num_stripes=4)
    m.put("alice", 100)
    assert m.compute("alice", lambda old: old + 5) == 105
    assert m.compute("bob", lambda old: (old or 0) + 1) == 1
    m.transfer("alice", "bob", 30)
    assert m.get("alice") == 75 and m.get("bob") == 31
    assert m.total() == 106 and len(m) == 2


def test_stripe_of():
    m = StripedHashMap(num_stripes=8)
    for k in [0, 1, 7, 8, 123, -5, "x", (1, 2)]:
        assert m.stripe_of(k) == hash(k) % 8


def test_matches_a_dict():
    rng = random.Random(21)
    m, ref = StripedHashMap(num_stripes=8), {}
    for _ in range(5000):
        k = rng.randint(0, 60)
        r = rng.random()
        if r < 0.35:
            v = rng.randint(0, 9)
            m.put(k, v)
            ref[k] = v
        elif r < 0.55:
            assert m.delete(k) == (k in ref)
            ref.pop(k, None)
        elif r < 0.75:
            new = m.compute(k, lambda old: None if old == 3 else (old or 0) + 1)
            want = None if ref.get(k) == 3 else ref.get(k, 0) + 1
            assert new == want
            if want is None:
                ref.pop(k, None)
            else:
                ref[k] = want
        else:
            assert m.get(k, "missing") == ref.get(k, "missing")
        assert len(m) == len(ref)
    assert m.total() == sum(ref.values())


def test_put_overwrites_and_none_values_from_put_are_kept():
    m = StripedHashMap(num_stripes=2)
    m.put("a", 1)
    m.put("a", 2)
    m.put("b", None)
    assert m.get("a") == 2 and m.get("b", "missing") is None and len(m) == 2
    assert m.delete("b") and not m.delete("b") and len(m) == 1


def test_compute_returning_none_removes():
    m = StripedHashMap()
    m.put("k", 5)
    assert m.compute("k", lambda old: None) is None
    assert m.get("k", "gone") == "gone" and len(m) == 0
    assert m.compute("never", lambda old: None) is None and len(m) == 0


def test_transfer_rules():
    m = StripedHashMap(num_stripes=4)
    m.put("a", 10)
    m.transfer("a", "b", 10)
    assert m.get("a") == 0 and m.get("b") == 10 and len(m) == 2
    with pytest.raises(ValueError):
        m.transfer("a", "b", 1)
    with pytest.raises(ValueError):
        m.transfer("b", "a", -1)
    with pytest.raises(ValueError):
        m.transfer("nobody", "a", 1)
    assert m.get("a") == 0 and m.get("b") == 10 and m.get("nobody", "missing") == "missing"
    m.transfer("b", "b", 4)
    assert m.get("b") == 10
    assert m.total() == 10


# ---- Which locks, how many, in what order ----------------------------------
def test_single_key_operations_take_exactly_their_stripe_lock():
    m, t = tracked(16)
    for k in range(200):
        s = k % 16  # hash(k) == k for small ints
        for op in (lambda: m.put(k, k), lambda: m.get(k), lambda: m.compute(k, lambda v: v + 1), lambda: m.delete(k)):
            t.reset()
            op()
            assert t.acquired == [s], f"key {k}: took locks {t.acquired}, expected exactly [{s}]"
            assert not t.held, "a lock was not released"


def test_keys_spread_over_all_stripes():
    m, t = tracked(16)
    for k in range(1024):
        m.put(k * 7, k)
    per = [t.acquired.count(s) for s in range(16)]
    assert min(per) == 64 and max(per) == 64, f"lock use per stripe: {per}: are all keys sharing one lock?"


def test_len_takes_no_lock():
    m, t = tracked(8)
    for k in range(100):
        m.put(k, k)
    t.reset()
    assert len(m) == 100
    assert t.acquired == [], f"len() took locks {t.acquired}: sum per-stripe counts instead"


def test_compute_runs_under_its_lock_and_once():
    m, t = tracked(16)
    calls = []

    def fn(old):
        calls.append(list(t.held))
        return (old or 0) + 1

    for k in [5, 21, 37]:
        m.compute(k, fn)
    assert calls == [[5], [5], [5]], f"fn ran with locks held = {calls}: it must run once, inside the key's stripe lock"


def test_compute_error_releases_the_lock_and_changes_nothing():
    m, t = tracked(4)
    m.put("x", 1)

    def boom(old):
        raise KeyError("nope")

    with pytest.raises(KeyError):
        m.compute("x", boom)
    assert not t.held, "the lock must be released when fn raises"
    assert m.get("x") == 1


def test_transfer_locks_in_increasing_order():
    m, t = tracked(16)
    m.put(9, 100)
    m.put(2, 100)
    t.reset()
    m.transfer(9, 2, 5)  # src is in the higher stripe
    assert t.acquired == [2, 9], f"took {t.acquired}: take the lower stripe first"
    t.reset()
    m.transfer(2, 9, 5)
    assert t.acquired == [2, 9]
    assert not t.held and m.get(9) == 100 and m.get(2) == 100


def test_transfer_within_one_stripe_takes_its_lock_once():
    m, t = tracked(16)
    m.put(3, 50)
    t.reset()
    m.transfer(3, 19, 20)  # 3 and 19 are both stripe 3
    assert t.acquired == [3]
    assert m.get(3) == 30 and m.get(19) == 20


def test_failed_transfer_releases_its_locks():
    m, t = tracked(16)
    m.put(1, 5)
    with pytest.raises(ValueError):
        m.transfer(1, 14, 6)
    assert not t.held, "locks still held after the ValueError"
    assert m.get(1) == 5 and m.get(14, "missing") == "missing"


def test_total_holds_every_lock_at_once():
    m, t = tracked(16)
    for k in range(40):
        m.put(k, 2)
    t.reset()
    assert m.total() == 80
    assert t.acquired == list(range(16)), f"total() took {t.acquired}: take all 16, in order"
    assert t.most_held == 16, "hold every stripe at the same moment, or a transfer can slip in between"
    assert not t.held


# ---- Real threads, real locks -----------------------------------------------
def run_threads(targets):
    errors = []

    def wrap(fn):
        def go():
            try:
                fn()
            except BaseException as e:  # reported below
                errors.append(e)
        return go

    threads = [threading.Thread(target=wrap(f), daemon=True) for f in targets]
    for th in threads:
        th.start()
    for th in threads:
        th.join(15)
    assert not any(th.is_alive() for th in threads), "threads still running after 15 s: deadlock?"
    assert not errors, repr(errors[0])


def test_no_lost_updates_with_threads():
    m = StripedHashMap(num_stripes=8)
    keys = list(range(64))

    def worker(seed):
        rng = random.Random(seed)
        def go():
            for _ in range(3000):
                m.compute(rng.choice(keys), lambda old: (old or 0) + 1)
        return go

    run_threads([worker(s) for s in range(8)])
    assert m.total() == 8 * 3000
    assert len(m) == 64


def test_transfers_conserve_money_and_do_not_deadlock():
    m = StripedHashMap(num_stripes=8)
    accounts = list(range(40))
    for a in accounts:
        m.put(a, 100)
    seen = []
    stop = threading.Event()

    def mover(seed):
        rng = random.Random(seed)
        def go():
            for _ in range(2000):
                a, b = rng.sample(accounts, 2)
                try:
                    m.transfer(a, b, rng.randint(1, 30))
                except ValueError:
                    pass  # not enough money: fine
        return go

    def auditor():
        while not stop.is_set():
            seen.append(m.total())

    movers = [mover(s) for s in range(6)]
    audit = threading.Thread(target=auditor, daemon=True)
    audit.start()
    try:
        run_threads(movers)
    finally:
        stop.set()
        audit.join(5)
    assert m.total() == 4000
    assert seen and set(seen) == {4000}, f"total() saw {sorted(set(seen))[:5]}: it must be one consistent snapshot"
    assert all(m.get(a) >= 0 for a in accounts)
