import ast
import inspect
import random
import signal
import weakref

import pytest

import external_sort as solution
from external_sort import external_sort


@pytest.fixture(autouse=True)
def time_limit():
    """Every test takes a few seconds at most (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 30 s cap")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(30)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------- the pretend disk


class DiskRuleBroken(Exception):
    pass


class Key:
    """A sort key that counts every comparison made with it."""

    __slots__ = ("_v",)
    compares = 0

    def __init__(self, v):
        self._v = v

    def _c(self, other):
        Key.compares += 1
        return other._v

    def __lt__(self, other): return self._v < self._c(other)
    def __le__(self, other): return self._v <= self._c(other)
    def __gt__(self, other): return self._v > self._c(other)
    def __ge__(self, other): return self._v >= self._c(other)
    def __eq__(self, other): return isinstance(other, Key) and self._v == self._c(other)
    def __ne__(self, other): return not self.__eq__(other)
    def __hash__(self): return hash(("Key", self._v))  # consistent with ==, but says nothing about order
    def __repr__(self): return "Key(?)"  # opaque: printing a key must not leak its value


class Record:
    """One record in RAM. Records are not comparable; compare their .key."""

    __slots__ = ("key", "value", "_disk", "__weakref__")

    def __init__(self, disk, k, v):
        self.key, self.value, self._disk = Key(k), v, disk
        disk._born()

    def __del__(self):
        self._disk.live -= 1

    def __repr__(self):
        return f"Record(key=?, value={self.value!r})"


class Reader:
    def __init__(self, disk, name):
        self.disk, self.data, self.i, self.open = disk, disk.files[name], 0, True
        disk.open_readers += 1
        if disk.open_readers > disk.fan_in:
            disk.open_readers -= 1
            self.open = False
            raise DiskRuleBroken(f"more than fan_in = {disk.fan_in} files open for reading at once; close() the ones you're done with")

    def __iter__(self):
        return self

    def __next__(self):
        if not self.open:
            raise StopIteration
        if self.i >= len(self.data):
            self.close()
            raise StopIteration
        k, v = self.data[self.i]
        self.i += 1
        self.disk.reads += 1
        if self.disk.reads > self.disk.read_budget:
            raise DiskRuleBroken(f"over the read budget of {self.disk.read_budget:,} records: {self.disk.passes_hint}")
        rec = Record(self.disk, k, v)
        self.disk._issued.add(rec)
        return rec

    def close(self):
        if self.open:
            self.open = False
            self.disk.open_readers -= 1

    def __del__(self):
        self.close()


class Writer:
    def __init__(self, disk, name):
        self.disk, self.name = disk, name
        disk.files[name] = self.data = []

    def write(self, rec):
        if not isinstance(rec, Record) or rec not in self.disk._issued:
            raise DiskRuleBroken("write() takes a record you read from this disk, not a key or a copy")
        self.disk.writes += 1
        if self.disk.writes > self.disk.write_budget:
            raise DiskRuleBroken(f"over the write budget of {self.disk.write_budget:,} records: {self.disk.passes_hint}")
        self.data.append((rec.key._v, rec.value))

    def close(self):
        pass


class Disk:
    def __init__(self, keys, memory, fan_in):
        self.n, self.memory, self.fan_in = len(keys), memory, fan_in
        self.files = {"input": [(k, i) for i, k in enumerate(keys)]}
        self.reads = self.writes = self.live = self.peak_live = self.open_readers = 0
        self._issued = weakref.WeakSet()
        self._next = 0
        runs = -(-self.n // memory)
        passes = 0
        while runs > 1:  # by construction: each pass divides the run count by fan_in
            runs = -(-runs // fan_in)
            passes += 1
        self.passes = passes
        self.read_budget = self.write_budget = self.n * (1 + passes)
        self.passes_hint = (f"{self.n} records, memory {memory}, fan_in {fan_in} allow 1 run pass + {passes} merge "
                            f"pass(es); are your runs full-size, and do you merge fan_in runs at a time?")

    def _born(self):
        self.live += 1
        self.peak_live = max(self.peak_live, self.live)
        if self.live > self.memory + 1:
            raise DiskRuleBroken(f"more than memory + 1 = {self.memory + 1} records alive in RAM at once "
                                  f"(is an old buffer, or a list of all records, still referenced?)")

    def reader(self, name):
        return Reader(self, name)

    def writer(self):
        self._next += 1
        return Writer(self, f"file-{self._next}")



def run_sort(keys, memory, fan_in):
    disk = Disk(keys, memory, fan_in)
    Key.compares = 0
    out = external_sort(disk, "input", memory, fan_in)
    assert isinstance(out, str) and out in disk.files, "return the name of the output file on the disk"
    got = disk.files[out]
    expected = sorted(disk.files["input"])  # (key, original position): sorted and stable
    assert len(got) == len(expected), f"output has {len(got)} records, input had {len(expected)}"
    assert got == expected, "output is not sorted by key, or equal keys lost their input order (stability)"
    return disk


# ---------------------------------------------------------------- tests


def test_example_two_merge_passes():
    rng = random.Random(1)
    keys = [rng.randrange(10**6) for _ in range(10_000)]
    disk = run_sort(keys, memory=100, fan_in=10)
    assert disk.passes == 2
    assert disk.reads == disk.writes == 30_000


def test_small_fan_in_needs_more_passes():
    rng = random.Random(2)
    keys = [rng.randrange(10**6) for _ in range(10_000)]
    disk = run_sort(keys, memory=100, fan_in=4)  # 100 -> 25 -> 7 -> 2 -> 1
    assert disk.passes == 4


def test_fan_in_two():
    rng = random.Random(3)
    disk = run_sort([rng.randrange(1000) for _ in range(800)], memory=100, fan_in=2)
    assert disk.passes == 3


def test_uneven_last_run():
    rng = random.Random(4)
    run_sort([rng.randrange(10**6) for _ in range(10_001)], memory=100, fan_in=10)  # 101 runs, 3 passes
    run_sort([rng.randrange(10**6) for _ in range(101)], memory=100, fan_in=10)  # 2 runs, 1 pass


@pytest.mark.parametrize("n", [0, 1, 2, 49, 50])
def test_fits_in_one_run(n):
    rng = random.Random(n)
    disk = run_sort([rng.randrange(100) for _ in range(n)], memory=50, fan_in=5)
    assert disk.reads == disk.writes == n, "one run is already the sorted file: read once, write once"


def test_many_duplicates_stay_stable():
    rng = random.Random(5)
    run_sort([rng.randrange(5) for _ in range(3000)], memory=64, fan_in=8)
    run_sort([7] * 1000, memory=30, fan_in=6)


def test_sorted_and_reversed_input():
    run_sort(list(range(5000)), memory=50, fan_in=10)
    run_sort(list(range(5000, 0, -1)), memory=50, fan_in=10)


def test_memory_rule_is_enforced():
    # A sanity check of the disk itself: reading everything into a list breaks the rule.
    disk = Disk(list(range(500)), memory=50, fan_in=5)
    with pytest.raises(DiskRuleBroken):
        list(disk.reader("input"))


def test_heap_not_linear_scan_over_fronts():
    rng = random.Random(6)
    memory, fan_in = 260, 256
    n = memory * fan_in  # 256 full runs: exactly one merge pass
    keys = [rng.randrange(10**9) for _ in range(n)]
    disk = run_sort(keys, memory=memory, fan_in=fan_in)
    assert disk.passes == 1
    per_record = Key.compares / n
    assert per_record <= 120, (
        f"{per_record:.0f} key comparisons per record. Sorting runs of 260 costs about 8; a heap over 256 fronts "
        f"about 16 to 32 more. Scanning all 256 fronts for the smallest costs 255."
    )


# ---------------------------------------------------------------- fair play


# The tests measure time, memory and work. A solution has no reason to import
# the measuring tools or the tests themselves.
OFF_LIMITS = {"tracemalloc", "gc", "signal", "ctypes"}


def imported_modules(module):
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    return names


def test_does_not_import_the_measuring_tools():
    bad = sorted(n for n in imported_modules(solution) if n in OFF_LIMITS or n.startswith("test_"))
    assert not bad, f"the solution doesn't need these imports: {bad}"


def test_uses_only_the_disk_api():
    # disk.files holds the raw data and key._v the raw key: reading either
    # skips the read and comparison counts the tests rely on.
    used = {node.attr for node in ast.walk(ast.parse(inspect.getsource(solution))) if isinstance(node, ast.Attribute)}
    bad = sorted(used & {"files", "_v"})
    assert not bad, f"use only reader(), writer(), write(), close(), .name, .key and .value, not {bad}"
