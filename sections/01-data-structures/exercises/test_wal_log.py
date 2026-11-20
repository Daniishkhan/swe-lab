import random
import signal

import pytest

from wal_log import LogFile, PowerLoss, WalStore


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a second when every change appends one record (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is every put rewriting or re-reading the whole log?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


NASTY = ["", "a=b", "line\nbreak", "tab\there", "\x00nul", "emoji \U0001F600", "é" * 40, "P\tk\tv\n", "x" * 3000]


def test_example():
    log = LogFile()
    s = WalStore(log)
    s.put("user:1", "Ada")
    s.put("user:2", "Linus")
    s.delete("user:1")
    log.crash()
    s = WalStore(log)
    assert s.get("user:2") == "Linus"
    assert s.get("user:1") is None
    assert s.get("user:1", "gone") == "gone"


def test_empty_log():
    log = LogFile()
    s = WalStore(log)
    assert s.get("x") is None
    s.delete("never-existed")
    assert WalStore(log).get("never-existed") is None


def test_overwrite_and_delete_then_put_again():
    log = LogFile()
    s = WalStore(log)
    s.put("k", "1")
    s.put("k", "2")
    s.delete("k")
    s.put("k", "3")
    assert s.get("k") == "3"
    assert WalStore(log).get("k") == "3"


def test_any_string_survives_a_restart():
    log = LogFile()
    s = WalStore(log)
    for i, k in enumerate(NASTY):
        for j, v in enumerate(NASTY):
            s.put(k + str(j), v + str(i))
    s2 = WalStore(log)
    for i, k in enumerate(NASTY):
        for j, v in enumerate(NASTY):
            assert s2.get(k + str(j)) == v + str(i), (k, v)


def test_acknowledged_changes_survive_a_crash():
    rng = random.Random(1)
    log = LogFile(seed=1)
    s, ref = WalStore(log), {}
    for step in range(400):
        k = f"k{rng.randrange(60)}"
        if rng.random() < 0.2:
            s.delete(k)
            ref.pop(k, None)
        elif rng.random() < 0.1:
            batch = [(f"k{rng.randrange(60)}", str(rng.random())) for _ in range(rng.randrange(1, 6))]
            s.put_many(batch)
            ref.update(batch)
        else:
            v = str(rng.random())
            s.put(k, v)
            ref[k] = v
        if step % 37 == 0:
            log.crash(garbage=step % 2 == 0)
            s = WalStore(log)
            assert {k: s.get(k) for k in ref} == ref
            assert all(s.get(f"k{i}") is None for i in range(60) if f"k{i}" not in ref)


def replay_states(ops):
    """states[i] = the store after the first i records."""
    states, cur = [{}], {}
    for op in ops:
        cur = dict(cur)
        if op[0] == "put":
            cur[op[1]] = op[2]
        else:
            cur.pop(op[1], None)
        states.append(cur)
    return states


def snapshot(s, keys):
    return {k: s.get(k) for k in keys if s.get(k) is not None}


@pytest.mark.parametrize("seed", range(6))
def test_power_loss_during_fsync(seed):
    """Lose power in the middle of an fsync, reopen, keep going, many times."""
    rng = random.Random(seed)
    log = LogFile(seed=seed)
    s = WalStore(log)
    records = []      # every record ever started, in order
    acked = 0         # how many of them were acknowledged (their call returned)
    keys = [f"key{i}" for i in range(25)] + NASTY[:4]
    for _ in range(60):
        log.crash_at_fsync = rng.randint(1, 8)
        try:
            for _ in range(50):  # ends early when the power goes
                kind = rng.random()
                if kind < 0.6:
                    rec = [("put", rng.choice(keys), rng.choice(NASTY) + str(rng.random()))]
                    records += rec
                    s.put(rec[0][1], rec[0][2])
                elif kind < 0.8:
                    rec = [("del", rng.choice(keys))]
                    records += rec
                    s.delete(rec[0][1])
                else:
                    rec = [("put", rng.choice(keys), str(rng.random())) for _ in range(rng.randint(1, 5))]
                    records += rec
                    s.put_many([(k, v) for _, k, v in rec])
                acked = len(records)
        except PowerLoss:
            pass
        s = WalStore(log)
        states = replay_states(records)
        got = snapshot(s, keys)
        ok = [i for i in range(acked, len(records) + 1) if states[i] == got]
        assert ok, f"after a power loss the store holds {len(got)} keys that match no prefix of the log from the {acked} acknowledged records on"
        records = records[:ok[-1]]  # the records that survived are the history now
        acked = len(records)


def test_new_records_after_a_torn_tail_are_kept():
    for seed in range(40):
        log = LogFile(seed=seed)
        s = WalStore(log)
        s.put("a", "1")
        log.crash_at_fsync = 1
        with pytest.raises(PowerLoss):
            s.put("b", "x" * 200)
        s = WalStore(log)                       # recovery: the torn record must be cut off here
        s.put("c", "3")
        s = WalStore(log)                       # a clean restart
        assert s.get("a") == "1" and s.get("c") == "3", f"seed {seed}: a record written after a torn tail was lost"


# ---- work ----
def test_one_record_and_one_fsync_per_change():
    log = LogFile()
    s = WalStore(log)
    rng = random.Random(5)
    payload = 0
    for i in range(3000):
        k, v = f"user:{rng.randrange(500)}", "v" * rng.randrange(40)
        before = log.fsyncs
        if i % 5 == 0:
            s.delete(k)
            payload += len(k.encode()) + 32
        else:
            s.put(k, v)
            payload += len(k.encode()) + len(v.encode()) + 32
        assert log.fsyncs == before + 1, "each put or delete must fsync exactly once before it returns"
    assert log.bytes_appended <= payload, f"{log.bytes_appended:,} bytes appended for 3,000 changes (budget {payload:,}): append one record, don't rewrite the store"


def test_put_many_is_one_fsync():
    log = LogFile()
    s = WalStore(log)
    pairs = [(f"k{i}", str(i)) for i in range(1000)]
    before = log.fsyncs
    s.put_many(pairs)
    assert log.fsyncs - before == 1, f"{log.fsyncs - before} fsyncs for one batch: group commit means one"
    s.put_many([])
    assert log.fsyncs - before <= 2
    s2 = WalStore(log)
    assert all(s2.get(k) == v for k, v in pairs)
    assert log.bytes_appended <= sum(len(k) + len(v) + 32 for k, v in pairs)


def test_get_reads_nothing_and_open_reads_once():
    log = LogFile()
    s = WalStore(log)
    s.put_many((f"k{i}", "x" * 50) for i in range(2000))
    size = log.size()
    log.bytes_read = 0
    for i in range(2000):
        assert s.get(f"k{i}") == "x" * 50
    assert log.bytes_read == 0, "get must answer from memory"
    WalStore(log)
    assert log.bytes_read <= 2 * size, f"opening read {log.bytes_read:,} bytes of a {size:,}-byte log"


def test_many_changes_quickly():
    log = LogFile()
    s = WalStore(log)
    for i in range(50_000):
        s.put(f"key{i % 5000}", str(i))
    s = WalStore(log)
    assert s.get("key4999") == "49999" and s.get("key0") == "45000"
