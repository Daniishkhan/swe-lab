import random
import signal
import tracemalloc

import pytest

from bitset import Bitset


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes about a second at most when no call walks every position (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: does len, |, &, - or iter walk every position from 0 to size? "
                           "Use one int operation, and for iter one step per member.")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def as_int(members):
    v = 0
    for i in members:
        v |= 1 << i
    return v


# ---------- Basics ----------

def test_example():
    b = Bitset(10, [0, 3])
    assert b.bits == 0b1001
    assert 3 in b and 0 in b and 1 not in b
    assert len(b) == 2
    b.add(9)
    assert b.bits == 0b1000001001
    assert list(b) == [0, 3, 9]
    b.discard(3)
    assert list(b) == [0, 9] and b.bits == 0b1000000001


def test_empty_and_size_zero():
    b = Bitset(0)
    assert b.bits == 0 and len(b) == 0 and list(b) == [] and 0 not in b
    with pytest.raises(IndexError):
        b.add(0)
    e = Bitset(5)
    assert e.bits == 0 and len(e) == 0 and list(e) == []


def test_add_twice_counts_once():
    b = Bitset(8)
    b.add(5)
    b.add(5)
    assert len(b) == 1 and b.bits == 32


def test_discard_absent_is_a_no_op():
    b = Bitset(8, [1, 2])
    b.discard(5)
    assert b.bits == 0b110, "discarding an absent member must not add it (XOR toggles: use & ~)"
    b.discard(100)
    b.discard(-1)
    assert b.bits == 0b110


def test_bounds():
    b = Bitset(8)
    for bad in (8, 9, -1, 1000):
        with pytest.raises(IndexError):
            b.add(bad)
    with pytest.raises(IndexError):
        Bitset(4, [1, 4])
    assert 8 not in b and -1 not in b and 7 not in b
    b.add(7)
    assert 7 in b and 8 not in b


def test_set_ops_new_objects_and_sizes():
    a = Bitset(16, [1, 2, 3, 10])
    c = Bitset(16, [2, 3, 4, 15])
    u, i, d = a | c, a & c, a - c
    assert list(u) == [1, 2, 3, 4, 10, 15]
    assert list(i) == [2, 3]
    assert list(d) == [1, 10]
    assert list(c - a) == [4, 15]
    assert a.bits == as_int([1, 2, 3, 10]) and c.bits == as_int([2, 3, 4, 15]), "don't change the operands"
    assert all(isinstance(x, Bitset) for x in (u, i, d))
    u.add(0)
    assert 0 not in a and 0 not in c, "the result must be a new Bitset, not one of the operands"
    with pytest.raises(ValueError):
        a | Bitset(17)
    with pytest.raises(ValueError):
        a & Bitset(15)
    with pytest.raises(ValueError):
        a - Bitset(8)


def test_equality():
    assert Bitset(10, [1, 5]) == Bitset(10, [5, 1])
    assert Bitset(10, [1, 5]) != Bitset(10, [1])
    assert Bitset(10, [1, 5]) != Bitset(11, [1, 5]), "different sizes are different bitsets"
    assert Bitset(3) != "not a bitset"


def test_matches_python_set():
    rng = random.Random(21)
    for _ in range(60):
        size = rng.randint(1, 300)
        ref_a, ref_b = set(), set()
        a, b = Bitset(size), Bitset(size)
        for _ in range(200):
            op, i = rng.random(), rng.randrange(size)
            target, ref = (a, ref_a) if rng.random() < 0.5 else (b, ref_b)
            if op < 0.6:
                target.add(i); ref.add(i)
            else:
                target.discard(i); ref.discard(i)
        for bs, ref in ((a, ref_a), (b, ref_b)):
            assert bs.bits == as_int(ref)
            assert list(bs) == sorted(ref)
            assert len(bs) == len(ref)
            assert all((i in bs) == (i in ref) for i in range(-2, size + 2))
        assert list(a | b) == sorted(ref_a | ref_b)
        assert list(a & b) == sorted(ref_a & ref_b)
        assert list(a - b) == sorted(ref_a - ref_b)


# ---------- Work and memory ----------

BIG = 1_000_000


def sparse(members):
    return Bitset(BIG, members)


def test_len_does_not_walk_every_position():
    b = sparse([5, 400_000, 999_999])
    for _ in range(1000):
        assert len(b) == 3


def test_set_ops_do_not_walk_every_position():
    a = sparse([1, 500_000, 999_998])
    c = sparse([500_000, 777_777])
    for _ in range(1000):
        u, i, d = a | c, a & c, a - c
    assert list(u) == [1, 500_000, 777_777, 999_998]
    assert list(i) == [500_000]
    assert list(d) == [1, 999_998]


def test_iter_takes_one_step_per_member():
    members = [7, 250_000, 600_001, 999_999]
    b = sparse(members)
    for _ in range(1000):
        assert list(b) == members


def test_iter_dense():
    b = Bitset(20_000, range(0, 20_000, 3))
    assert list(b) == list(range(0, 20_000, 3))


def test_dense_bitset_is_packed():
    size = 200_000
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        b = Bitset(size, range(0, size, 2))
        held = tracemalloc.get_traced_memory()[0] - base
    finally:
        tracemalloc.stop()
    assert len(b) == size // 2
    packed = size // 8
    assert held <= 2 * packed + 4096, (
        f"a Bitset of {size:,} positions with {size // 2:,} members holds {held:,} bytes. "
        f"Packed bits need about {packed:,} (one bit each). A set of ints, a list of booleans or a "
        "bytearray of 0/1 costs 8 to 200 times that. Keep only the one int in self.bits.")
