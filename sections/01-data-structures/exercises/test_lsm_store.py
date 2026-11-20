import random
import signal

import pytest

from lsm_store import BLOCK, MISSING, TOMBSTONE, BlockFile, LSMStore, SSTable


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something re-reading every table?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


@pytest.fixture(autouse=True)
def reset_counters():
    BlockFile.reads = BlockFile.written = 0
    yield


def counted(fn):
    before = BlockFile.reads
    out = fn()
    return out, BlockFile.reads - before


# ---- SSTable ----
def test_sstable_get_reads_one_block():
    items = [(k, k * 10) for k in range(0, 200, 2)]  # 100 pairs: 7 blocks
    t = SSTable(items)
    assert BlockFile.written == 100
    for k in range(-3, 203):
        got, reads = counted(lambda: t.get(k))
        assert got == (k * 10 if 0 <= k < 200 and k % 2 == 0 else MISSING), k
        assert reads <= 1, f"get({k}) read {reads} blocks: the sparse index says which one"
        if k < 0 or k > 198:
            assert reads == 0, f"get({k}) read a block, but {k} is outside the table's fence keys [0, 198]"


def test_sstable_iter_from():
    items = [(k, str(k)) for k in range(0, 300, 3)]  # 100 pairs
    t = SSTable(items)
    assert list(t.iter_from(-5)) == items
    assert list(t.iter_from(150)) == [(k, v) for k, v in items if k >= 150]
    assert list(t.iter_from(1000)) == []
    _, reads = counted(lambda: list(t.iter_from(250)))
    assert reads <= 2, f"iter_from(250) read {reads} blocks: start at the block that holds 250"
    it = t.iter_from(30)
    _, reads = counted(lambda: [next(it) for _ in range(3)])
    assert reads <= 1, "iter_from must be lazy: 3 items come from one block"


def test_sstable_empty_and_tombstones():
    t = SSTable([])
    assert t.get(1) is MISSING and list(t.iter_from(0)) == []
    t = SSTable([("a", TOMBSTONE), ("b", 1)])
    assert t.get("a") is TOMBSTONE and t.get("b") == 1 and t.get("c") is MISSING


# ---- LSMStore: correctness ----
def test_example():
    s = LSMStore(memtable_limit=3)
    s.put("a", 1); s.put("c", 3); s.put("b", 2)
    assert len(s.tables) == 1
    s.put("a", 9); s.delete("c"); s.put("d", 4)
    assert len(s.tables) == 2
    assert s.get("a") == 9 and s.get("c") is None and s.get("b") == 2 and s.get("d") == 4
    assert s.get("c", "gone") == "gone"
    assert list(s.items()) == [("a", 9), ("b", 2), ("d", 4)]
    s.compact()
    assert len(s.tables) == 1 and list(s.items()) == [("a", 9), ("b", 2), ("d", 4)]
    assert BlockFile.written == 3 + 3 + 3


def test_flush_rules():
    s = LSMStore(memtable_limit=4)
    for k in "abc":
        s.put(k, 1)
    s.put("a", 2)                       # an update doesn't grow the memtable
    assert s.tables == [] and BlockFile.written == 0, "nothing reaches the disk before the memtable is full"
    s.put("d", 1)
    assert len(s.tables) == 1 and BlockFile.written == 4
    s.flush()
    assert len(s.tables) == 1, "flushing an empty memtable makes no table"
    s.delete("zz")
    s.flush()
    assert len(s.tables) == 2 and s.get("zz") is None


def test_random_against_a_dict():
    rng = random.Random(3)
    for limit in (1, 2, 5, 16, 40):
        s, ref = LSMStore(memtable_limit=limit), {}
        for step in range(1500):
            k = rng.randrange(120)
            r = rng.random()
            if r < 0.25:
                s.delete(k)
                ref.pop(k, None)
            else:
                s.put(k, step)
                ref[k] = step
            if step % 500 == 499:
                s.compact()
                assert len(s.tables) <= 1
            if step % 50 == 0:
                lo, hi = sorted((rng.randrange(-5, 125), rng.randrange(-5, 125)))
                assert list(s.items(lo, hi)) == sorted((k, v) for k, v in ref.items() if lo <= k < hi)
        assert [s.get(k) for k in range(-2, 125)] == [ref.get(k) for k in range(-2, 125)]
        assert list(s.items()) == sorted(ref.items())


def test_strings_and_open_ended_ranges():
    s = LSMStore(memtable_limit=5)
    words = "pear fig apple kiwi plum date lime nut oat rye yam".split()
    for i, w in enumerate(words):
        s.put(w, i)
    s.delete("kiwi")
    want = sorted((w, i) for i, w in enumerate(words) if w != "kiwi")
    assert list(s.items()) == want
    assert list(s.items(lo="m")) == [p for p in want if p[0] >= "m"]
    assert list(s.items(hi="f")) == [p for p in want if p[0] < "f"]


# ---- LSMStore: work ----
def test_each_put_is_written_once():
    rng = random.Random(4)
    s = LSMStore(memtable_limit=100)
    n = 20_000
    for i in range(n):
        s.put(rng.randrange(1_000_000), i)
    assert BlockFile.written <= n, f"{BlockFile.written:,} pairs written for {n:,} puts: a flush writes the memtable once, never the old tables"
    assert len(s.tables) >= n // 100 - 1


def test_get_asks_newest_first_and_stops():
    s = LSMStore(memtable_limit=50)
    for rnd in range(50):                 # 50 tables, every one holds keys 0..49
        for k in range(50):
            s.put(k, (rnd, k))
    assert len(s.tables) == 50
    for k in range(50):
        got, reads = counted(lambda: s.get(k))
        assert got == (49, k)
        assert reads == 1, f"get({k}) read {reads} blocks: the newest table has it, so stop there"


def test_get_on_time_ordered_keys_reads_one_block():
    s = LSMStore(memtable_limit=100)
    for t in range(10_000):              # timestamps: each table covers its own range
        s.put(t, f"event {t}")
    assert len(s.tables) == 100
    for t in random.Random(5).sample(range(10_000), 300):
        got, reads = counted(lambda: s.get(t))
        assert got == f"event {t}"
        assert reads <= 1, f"get({t}) read {reads} blocks: fence keys rule out the 99 tables that can't hold it"
    for t in (-1, 10_000, 10 ** 9):
        _, reads = counted(lambda: s.get(t))
        assert reads == 0, f"get({t}) read {reads} blocks for a key outside every table"


def test_missing_key_reads_at_most_one_block_per_table():
    rng = random.Random(6)
    s = LSMStore(memtable_limit=200)
    for _ in range(6000):
        s.put(rng.randrange(0, 10 ** 6, 2), 1)   # even keys only
    tables = len(s.tables)
    for k in rng.sample(range(1, 10 ** 6, 2), 200):  # odd: never stored
        got, reads = counted(lambda: s.get(k))
        assert got is None
        assert reads <= tables, f"a missing key read {reads} blocks from {tables} tables"


def test_tombstone_ends_the_search():
    s = LSMStore(memtable_limit=10)
    for rnd in range(30):
        for k in range(10):
            s.put(k, rnd)
    s.delete(3)
    for k in range(100, 109):
        s.put(k, 0)                      # the tombstone for 3 is now in the newest table
    got, reads = counted(lambda: s.get(3))
    assert got is None
    assert reads == 1, f"get(3) read {reads} blocks: the tombstone in the newest table settles it"


def test_items_only_reads_what_overlaps():
    s = LSMStore(memtable_limit=100)
    for t in range(10_000):
        s.put(t, t)
    got, reads = counted(lambda: list(s.items(5_000, 5_100)))
    assert got == [(t, t) for t in range(5_000, 5_100)]
    assert reads <= 100 // BLOCK + 3, f"items over 100 keys read {reads} blocks: skip tables whose fence keys don't overlap"
    it = s.items(2_000)
    first, reads = counted(lambda: [next(it) for _ in range(3)])
    assert first == [(2_000, 2_000), (2_001, 2_001), (2_002, 2_002)]
    assert reads <= 81, f"3 items read {reads} blocks: items must be lazy (one block from each of the 80 overlapping tables is enough to start)"


def test_compact_reads_each_block_once_and_writes_live_keys_once():
    rng = random.Random(7)
    s = LSMStore(memtable_limit=64)
    ref = {}
    for i in range(8000):
        k = rng.randrange(2000)
        if rng.random() < 0.2:
            s.delete(k)
            ref.pop(k, None)
        else:
            s.put(k, i)
            ref[k] = i
    s.flush()
    blocks = BlockFile.written // BLOCK + len(s.tables)  # every block on disk, at most
    BlockFile.reads = BlockFile.written = 0
    s.compact()
    assert len(s.tables) == 1
    assert BlockFile.written == len(ref), f"compaction wrote {BlockFile.written:,} pairs for {len(ref):,} live keys: drop tombstones and old versions"
    assert BlockFile.reads <= blocks, f"compaction read {BlockFile.reads:,} blocks of {blocks:,}: read each one once"
    assert list(s.items()) == sorted(ref.items())
    for k in rng.sample(range(2000), 100):
        got, reads = counted(lambda: s.get(k))
        assert got == ref.get(k) and reads <= 1
