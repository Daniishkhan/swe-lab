"""
LSM key-value store
Topic: 01.13  |  Priority: P1

Problem
-------
Build sections 6 to 8 of the chapter: writes go to a memtable in memory;
a full memtable is flushed as one sorted, immutable SSTable; reads check the
memtable and then the tables, newest first; a delete writes a tombstone;
compaction merges the tables into one.

    s = LSMStore(memtable_limit=3)
    s.put("a", 1); s.put("c", 3); s.put("b", 2)   # 3 keys: flushed to table 1
    s.put("a", 9); s.delete("c"); s.put("d", 4)   # flushed to table 2
    s.get("a") -> 9          (table 2 is newer than table 1)
    s.get("c") -> None       (table 2 has a tombstone for c)
    s.get("b") -> 2
    list(s.items()) -> [("a", 9), ("b", 2), ("d", 4)]
    s.compact()              # now one table: a=9, b=2, d=4

(A real store also appends every put to a write-ahead log first, the
wal_log exercise. This one skips that, to stay about the LSM.)

The disk (given: read it, use it, don't change it)
-------------------------------------------------
BlockFile(blocks) writes an immutable file: a list of blocks, each a list
of at most BLOCK (16) (key, value) pairs. f.read_block(i) returns a copy
of block i; len(f) is the number of blocks. Two class-wide counters:
BlockFile.reads (blocks read) and BlockFile.written (pairs written).
TOMBSTONE marks a deleted key; MISSING means "this table doesn't have it".

Requirements
------------
SSTable(items): items are (key, value) pairs, sorted by key, keys unique.
  - Write them into ONE BlockFile, BLOCK pairs per block (the last block may
    be shorter). Keep in memory only a sparse index (the first key of each
    block) and the smallest and largest key: the "fence keys".
  - get(key): the value (maybe TOMBSTONE), or MISSING. Read at most one
    block, and none if the key is outside the fence keys.
  - iter_from(lo): a generator of the pairs with key >= lo, in order. Start
    at the right block (not block 0) and read each block at most once, lazily.
LSMStore(memtable_limit):
  - put(key, value), delete(key): into the memtable (a dict is fine; sort it
    when you flush). When the memtable holds memtable_limit keys, flush.
  - flush(): turn the memtable into a new SSTable (tombstones included) and
    put it at the front of self.tables (newest first). An empty memtable
    makes no table.
  - get(key, default=None): memtable first, then tables newest to oldest.
    The first table that knows the key decides: a value, or a tombstone
    (then the answer is default).
  - items(lo=None, hi=None): a generator of the live (key, value) pairs with
    lo <= key < hi, in key order: every source merged, newest version wins,
    tombstones hidden. Only touch tables whose fence keys overlap the range.
  - compact(): flush, then merge every table into one new SSTable. Newest
    wins; drop tombstones and overwritten values (safe here because the
    merge includes the oldest data). Afterwards self.tables has at most one.
- Keys only need < and ==. You may use heapq, including heapq.merge.

What the tests measure
----------------------
They count BlockFile.reads and BlockFile.written:
- Each put is written to disk once, at flush: 20,000 puts write at most
  20,000 pairs. Merging into one big table at every flush writes ~100x more.
- get reads at most one block per table it asks, and asks newest first: a
  key in the newest table costs 1 read even if 50 older tables have it too.
- On time-ordered keys (100 tables that don't overlap), get costs 1 read:
  the fence keys rule out the other 99 tables for free.
- A tombstone ends the search: older tables aren't read.
- items over 100 time-ordered keys reads about 100 / 16 blocks, not 100
  tables.
- compact reads every block once and writes each live key once.

Before you code (say it out loud)
---------------------------------
1. Why must get go newest to oldest, and why can it stop at the first hit?
2. Why can't delete just remove the key from the memtable?
3. When is it safe for compaction to drop a tombstone? (Here: always. Why
   not when merging only the two newest tables?)
4. Writes are fast here. What did reads pay for it, and what buys it back?

Run:  pytest -k lsm_store
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# The disk. Given: don't change it.
# ---------------------------------------------------------------------------
BLOCK = 16


class _Marker:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


TOMBSTONE = _Marker("TOMBSTONE")  # the value stored for a deleted key
MISSING = _Marker("MISSING")      # SSTable.get: "not in this table"


class BlockFile:
    """An immutable file of blocks. Counts blocks read and pairs written (class-wide)."""

    reads = 0
    written = 0

    def __init__(self, blocks):
        self._blocks = [list(b) for b in blocks]
        for b in self._blocks:
            if not 0 < len(b) <= BLOCK:
                raise ValueError(f"a block holds 1 to {BLOCK} pairs, got {len(b)}")
        BlockFile.written += sum(len(b) for b in self._blocks)

    def read_block(self, i: int) -> list:
        BlockFile.reads += 1
        return list(self._blocks[i])

    def __len__(self) -> int:
        return len(self._blocks)


# ---------------------------------------------------------------------------
# Yours.
# ---------------------------------------------------------------------------
class SSTable:
    def __init__(self, items):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def iter_from(self, lo):
        raise NotImplementedError


class LSMStore:
    def __init__(self, memtable_limit: int = 64):
        raise NotImplementedError

    def put(self, key, value) -> None:
        raise NotImplementedError

    def delete(self, key) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def items(self, lo=None, hi=None):
        raise NotImplementedError

    def compact(self) -> None:
        raise NotImplementedError
