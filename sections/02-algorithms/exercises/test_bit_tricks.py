import ast
import inspect
import random
import signal
import time
import tracemalloc

import pytest

import bit_tricks
from bit_tricks import add32, bit_positions, next_power_of_two, popcount, single_number


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes well under a second when done right (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: does a loop never end, or walk every bit position of a huge number? "
                           "In add32, Python ints never overflow, so a carry on negative numbers grows "
                           "forever unless you mask it to 32 bits.")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------- A counting int ----------

class B(int):
    """An int that counts every arithmetic, bitwise or comparison operation done
    with it (class-wide, in B.ops). Results are B again, so the count follows the
    value. Truth tests (while x:) and x.bit_length() are free."""

    ops = 0

    def __repr__(self):
        return f"B({int.__repr__(self)})"


def _wrap(name):
    base = getattr(int, name)

    def op(self, *args):
        B.ops += 1
        r = base(self, *args)
        return B(r) if isinstance(r, int) and not isinstance(r, bool) else r

    return op


def _wrap_divmod(name):
    base = getattr(int, name)

    def op(self, *args):
        B.ops += 1
        q, r = base(self, *args)
        return B(q), B(r)

    return op


B.__divmod__, B.__rdivmod__ = _wrap_divmod("__divmod__"), _wrap_divmod("__rdivmod__")

for _n in ("and", "or", "xor", "lshift", "rshift", "add", "sub", "mul", "floordiv", "mod", "pow"):
    for _p in ("", "r"):
        setattr(B, f"__{_p}{_n}__", _wrap(f"__{_p}{_n}__"))
for _n in ("invert", "neg", "pos", "abs", "eq", "ne", "lt", "le", "gt", "ge"):
    setattr(B, f"__{_n}__", _wrap(f"__{_n}__"))
B.__hash__ = int.__hash__


def counted(f, x):
    B.ops = 0
    r = f(B(x))
    return r, B.ops


# ---------- No strings, no bit_count ----------

def test_no_string_tricks():
    """Counting the '1's in bin(x), or calling x.bit_count(), skips the exercise."""
    tree = ast.parse(inspect.getsource(bit_tricks))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in {"bin", "hex", "oct", "format", "str", "repr"}:
            pytest.fail(f"line {node.lineno}: don't use {node.id}(): work on the bits, not on a string of them")
        if isinstance(node, ast.JoinedStr):
            pytest.fail(f"line {node.lineno}: no f-strings in this file: they turn the number into text")
        if isinstance(node, ast.Attribute) and node.attr == "bit_count":
            pytest.fail(f"line {node.lineno}: don't use .bit_count(): build it with bit operations")


# ---------- 4a. popcount ----------

def test_popcount_small():
    for x, want in [(0, 0), (1, 1), (2, 1), (3, 2), (13, 3), (255, 8), (256, 1), (1023, 10)]:
        assert popcount(B(x)) == want, f"popcount({x})"


def test_popcount_matches_slow_count():
    rng = random.Random(11)
    for _ in range(300):
        x = rng.getrandbits(rng.randint(1, 200))
        want = sum((x >> i) & 1 for i in range(x.bit_length()))
        assert popcount(B(x)) == want, f"popcount({x})"


@pytest.mark.parametrize("positions", [[0, 60], [1000], [0, 1000], [3, 64, 500, 999], list(range(0, 2000, 100))], ids=lambda p: f"{len(p)}ones")
def test_popcount_one_step_per_set_bit(positions):
    x = sum(1 << p for p in positions)
    r, ops = counted(popcount, x)
    k = len(positions)
    assert r == k
    assert ops <= 6 * k + 4, (
        f"{ops} operations for a {x.bit_length()}-bit number with only {k} ones. "
        f"Budget is {6 * k + 4}: a few per 1 bit. Looping over every position costs per position, "
        "not per 1 bit. What does x & (x - 1) do to x?")


# ---------- 4b. bit_positions ----------

def test_bit_positions_values():
    assert bit_positions(B(0)) == []
    assert bit_positions(B(13)) == [0, 2, 3]
    assert bit_positions(B(1 << 70)) == [70]
    rng = random.Random(12)
    for _ in range(300):
        x = rng.getrandbits(rng.randint(1, 150))
        want = [i for i in range(x.bit_length()) if (x >> i) & 1]
        assert bit_positions(B(x)) == want, f"bit_positions({x})"


@pytest.mark.parametrize("positions", [[0, 60], [1000], [5, 999], list(range(7, 2000, 150))], ids=lambda p: f"{len(p)}ones")
def test_bit_positions_one_step_per_set_bit(positions):
    x = sum(1 << p for p in positions)
    r, ops = counted(bit_positions, x)
    k = len(positions)
    assert list(r) == positions
    assert ops <= 8 * k + 4, (
        f"{ops} operations for a {x.bit_length()}-bit number with {k} ones. Budget is {8 * k + 4}: "
        "a few per 1 bit. Jump from one 1 to the next instead of walking the positions.")


def test_popcount_and_bit_positions_on_a_million_bit_plain_int():
    """A plain int this time: one step per 1 bit takes milliseconds, a step per position takes minutes."""
    x = (1 << 1_000_000) | (1 << 500_000) | 1
    start = time.perf_counter()
    assert popcount(x) == 3
    assert bit_positions(x) == [0, 500_000, 1_000_000]
    spent = time.perf_counter() - start
    assert spent < 1.0, (f"{spent:.1f} s for a number with 3 ones: something walks the 1,000,001 positions. "
                         "Jump from one 1 to the next.")


# ---------- 4c. next_power_of_two ----------

def test_next_power_of_two_values():
    assert next_power_of_two(B(1)) == 1
    assert next_power_of_two(B(5)) == 8
    assert next_power_of_two(B(8)) == 8
    assert next_power_of_two(B(9)) == 16
    assert next_power_of_two(B(2**100 + 1)) == 2**101
    assert next_power_of_two(B(2**100)) == 2**100
    p = 1
    for x in range(1, 5000):
        while p < x:
            p *= 2
        assert next_power_of_two(B(x)) == p, f"next_power_of_two({x})"


@pytest.mark.parametrize("x", [1, 2, 3, 1000, (1 << 1000) - 1, 1 << 1000, (1 << 1000) + 1], ids=lambda x: f"{x.bit_length()}bits")
def test_next_power_of_two_constant_work(x):
    _, ops = counted(next_power_of_two, x)
    assert ops <= 6, (f"{ops} operations (comparisons count) on a {x.bit_length()}-bit number: budget is 6 for any x. "
                      "x.bit_length() is free and says where the highest 1 is.")


# ---------- 5. single_number ----------

def test_single_number_examples():
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([-7]) == -7
    assert single_number([0, 5, 5]) == 0
    assert single_number([-3, 9, -3, 9, -1]) == -1


def test_single_number_random():
    rng = random.Random(5)
    for _ in range(200):
        pairs = rng.sample(range(-10**6, 10**6), rng.randint(0, 20))
        lone = rng.choice([v for v in range(-50, 50) if v not in pairs])
        nums = pairs + pairs + [lone]
        rng.shuffle(nums)
        assert single_number(nums) == lone


def test_single_number_constant_memory():
    rng = random.Random(7)
    pairs = rng.sample(range(-10**9, 10**9), 100_000)
    lone = 123_456_789_011
    nums = pairs + pairs + [lone]
    rng.shuffle(nums)
    before = list(nums)
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        got = single_number(nums)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    assert got == lone
    assert nums == before, "don't change the input list"
    assert peak <= 4096, (
        f"peak extra memory was {peak:,} bytes for 200,001 numbers. O(1) extra memory means a few "
        "hundred bytes, whatever n is. A set, dict, Counter or sorted copy grows with n. "
        "What does x ^ x equal?")


# ---------- 6. add32 ----------

def _is_constant(node):
    """A number literal, an ALL_CAPS name like MASK, or an expression of those, like (1 << 32)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int)
    if isinstance(node, ast.Name):
        return node.id.isupper()
    if isinstance(node, ast.UnaryOp):
        return _is_constant(node.operand)
    if isinstance(node, ast.BinOp):
        return _is_constant(node.left) and _is_constant(node.right)
    return False


def _add32_body_uses_plus_or_minus():
    """Scan add32 and every function of this module it calls. + or - with a constant on one
    side (u - (1 << 32), i += 1) is fine: it can't add a to b."""
    tree = ast.parse(inspect.getsource(bit_tricks))
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    todo, seen = ["add32"], set()
    while todo:
        name = todo.pop()
        if name in seen or name not in funcs:
            continue
        seen.add(name)
        for node in ast.walk(funcs[name]):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)) \
                    and not (_is_constant(node.left) or _is_constant(node.right)):
                return f"line {node.lineno} (in {name}): + or - between two numbers"
            if isinstance(node, ast.AugAssign) and isinstance(node.op, (ast.Add, ast.Sub)) \
                    and not _is_constant(node.value):
                return f"line {node.lineno} (in {name}): += or -= with a number that isn't a constant"
            if isinstance(node, ast.Name) and node.id == "sum":
                return f"line {node.lineno} (in {name}): sum()"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                todo.append(node.func.id)
    return None


def test_add32_no_plus_or_minus():
    bad = _add32_body_uses_plus_or_minus()
    assert bad is None, f"add32 must be built from bit operations, but it uses {bad}"


def wrap32(v):
    """What a 32-bit register holds after adding: keep the low 32 bits, read the top one as the sign."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >> 31 else v


def test_add32_examples():
    assert add32(2, 3) == 5
    assert add32(0, 0) == 0
    assert add32(-1, 1) == 0
    assert add32(-5, -7) == -12
    assert add32(100, -1) == 99


def test_add32_wraps_like_a_register():
    top, bottom = 2**31 - 1, -(2**31)
    assert add32(top, 1) == bottom
    assert add32(bottom, -1) == top
    assert add32(bottom, bottom) == 0
    assert add32(top, top) == -2


def test_add32_random():
    rng = random.Random(3)
    lo, hi = -(2**31), 2**31 - 1
    for _ in range(3000):
        a, b = rng.randint(lo, hi), rng.randint(lo, hi)
        assert add32(a, b) == wrap32(a + b), f"add32({a}, {b})"
    for _ in range(500):
        a, b = rng.randint(-1000, 1000), rng.randint(-1000, 1000)
        assert add32(a, b) == a + b, f"add32({a}, {b})"
