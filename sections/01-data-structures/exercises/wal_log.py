"""
Write-ahead log
Topic: 01.13  |  Priority: P2

Problem
-------
Build section 5 of the chapter: a key-value store that survives a crash.
Every change is appended to a log file and made durable (fsync) BEFORE the
call returns; the in-memory dict is only a copy you can rebuild. When the
store opens, it replays the log.

    log = LogFile()
    s = WalStore(log)
    s.put("user:1", "Ada")
    s.put("user:2", "Linus")
    s.delete("user:1")
    log.crash()                  # power loss
    s = WalStore(log)            # restart: replay the log
    s.get("user:2")  -> "Linus"
    s.get("user:1")  -> None

The disk file (given: read it, use it, don't change it)
------------------------------------------------------
LogFile is an append-only file. append(data) adds bytes at the end, but they
sit in the operating system's cache: a crash can lose them, or keep only a
part of them, until fsync() makes everything appended so far durable.
read_all() returns the whole file, size() its length, and truncate(n) cuts
it to n bytes (durably). crash() and the crash_at_fsync setting are for the
tests: they throw away, or tear, whatever wasn't fsynced.

Requirements
------------
- WalStore(log): open the store. Replay every record in the log to rebuild
  the dict. A crash can leave a torn last record: cut short, or ending in
  garbage. Stop at the first record that is incomplete or fails its
  checksum, and truncate the log there, so new records don't land after
  garbage.
- put(key, value) and delete(key): append ONE record for the change, fsync,
  then update the dict. When the call returns, the change survives any crash.
  Deleting a missing key is fine (it's still logged).
- put_many(pairs): one record per pair, then ONE fsync for the whole batch
  (group commit). After a crash during it, any prefix of the batch may
  survive; that's allowed.
- get(key, default=None): from the dict. No disk reads.
- Keys and values are str and may contain anything: newlines, tabs, "=",
  emoji, the empty string. Design a binary record: for example a header
  with the payload's length and a zlib.crc32 checksum, then the payload.
  (struct.pack and str.encode("utf-8") are your friends.)

What the tests measure
----------------------
- Durability: after put / delete / put_many return, a crash loses nothing.
- Crashes in the middle of an fsync, at hundreds of random points, some of
  them leaving garbage after the torn record: the store must reopen to the
  state after some prefix of the records, and never lose an acknowledged one.
- Bytes appended per change: about the size of the key and value plus a
  small header (32 bytes allowed). Rewriting the whole store on every put
  appends far more and fails.
- fsyncs: exactly one per put or delete, and one per put_many batch.
- get reads nothing from the log; opening reads the log about once.

Before you code (say it out loud)
---------------------------------
1. Why must the log record be durable before the change counts as done?
2. A text format like "key=value\n": which keys break it, and what does a
   torn last line look like?
3. What happens on the NEXT restart if you don't truncate a torn tail?
4. Why does one fsync for a batch of 100 puts make writes ~100x faster?
5. A crash can leave a run of zero bytes where a record was going to be,
   and zlib.crc32(b"") is 0. What does your reader make of a header that
   is all zeros?

Run:  pytest -k wal_log
"""

from __future__ import annotations

import random


# ---------------------------------------------------------------------------
# The disk file. Given: don't change it.
# ---------------------------------------------------------------------------
class PowerLoss(Exception):
    """The machine lost power in the middle of an fsync."""


class LogFile:
    def __init__(self, seed: int = 0):
        self._data = bytearray()
        self._synced = 0            # bytes [0, _synced) are on stable storage
        self._rng = random.Random(seed)
        self.crash_at_fsync = None  # tests: lose power during the n-th fsync from now
        self.bytes_appended = 0
        self.bytes_read = 0
        self.fsyncs = 0

    def append(self, data: bytes) -> None:
        self._data += data
        self.bytes_appended += len(data)

    def fsync(self) -> None:
        if self.crash_at_fsync is not None:
            self.crash_at_fsync -= 1
            if self.crash_at_fsync <= 0:
                self.crash_at_fsync = None
                self.crash(garbage=self._rng.random() < 0.5)
                raise PowerLoss("power lost during fsync")
        self.fsyncs += 1
        self._synced = len(self._data)

    def read_all(self) -> bytes:
        self.bytes_read += len(self._data)
        return bytes(self._data)

    def size(self) -> int:
        return len(self._data)

    def truncate(self, size: int) -> None:
        del self._data[size:]
        self._synced = min(self._synced, len(self._data))

    def crash(self, garbage: bool = False) -> None:
        """Power loss: of the bytes not yet fsynced, keep a random prefix,
        and with garbage=True fill the rest of their space with junk."""
        tail = len(self._data) - self._synced
        keep = self._rng.randint(0, tail)
        if garbage:
            junk = bytes(self._rng.choice([0, self._rng.randrange(256)]) for _ in range(tail - keep))
            self._data[self._synced + keep:] = junk
        else:
            del self._data[self._synced + keep:]
        self._synced = len(self._data)


# ---------------------------------------------------------------------------
# Your store.
# ---------------------------------------------------------------------------
class WalStore:
    def __init__(self, log: LogFile):
        raise NotImplementedError

    def put(self, key: str, value: str) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def put_many(self, pairs) -> None:
        raise NotImplementedError

    def get(self, key: str, default=None):
        raise NotImplementedError
