import random
import signal

import pytest

from mpmc_queue import EMPTY, AtomicRef, MSQueue, Node, run


@pytest.fixture(autouse=True)
def time_limit():
    """The whole file runs in a couple of seconds (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 20 s: is an operation looping forever?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


STEP_BUDGET = 60  # steps one operation may take when it runs alone


def run_alone(op, what):
    """Like run(), but fail if one operation takes more than STEP_BUDGET steps."""
    for _ in range(STEP_BUDGET):
        try:
            next(op)
        except StopIteration as done:
            return done.value
    raise AssertionError(f"{what} took over {STEP_BUDGET} steps running alone: is it waiting for a paused thread?")


def contents(q):
    """The values in the queue, oldest first, read through peek()."""
    head, tail = q.head.peek(), q.tail.peek()
    assert isinstance(head, Node) and isinstance(tail, Node), "self.head and self.tail must be AtomicRefs to Nodes"
    out, node, seen_tail = [], head.next.peek(), tail is head
    while node is not None:
        out.append(node.value)
        seen_tail = seen_tail or node is tail
        node = node.next.peek()
        assert len(out) < 100_000, "the list has a cycle"
    assert seen_tail, "tail points at a node that isn't in the list"
    return out


def drain(q):
    out = []
    while True:
        v = run_alone(q.dequeue(), "dequeue")
        if v is EMPTY:
            return out
        out.append(v)


# ---- Alone -----------------------------------------------------------------
def test_example():
    q = MSQueue()
    run(q.enqueue("a"))
    run(q.enqueue("b"))
    assert run(q.dequeue()) == "a"
    assert run(q.dequeue()) == "b"
    assert run(q.dequeue()) is EMPTY


def test_layout_dummy_head_and_tail():
    q = MSQueue()
    assert isinstance(q.head, AtomicRef) and isinstance(q.tail, AtomicRef)
    dummy = q.head.peek()
    assert isinstance(dummy, Node) and q.tail.peek() is dummy and dummy.next.peek() is None, \
        "an empty queue is one dummy node, with head and tail both pointing at it"
    for v in [1, 2, 3]:
        run(q.enqueue(v))
    assert contents(q) == [1, 2, 3]
    assert q.tail.peek().value == 3 and q.tail.peek().next.peek() is None
    assert run(q.dequeue()) == 1
    assert contents(q) == [2, 3]


def test_none_and_duplicates_are_values():
    q = MSQueue()
    for v in [None, 0, 0, None]:
        run(q.enqueue(v))
    assert drain(q) == [None, 0, 0, None]


def test_operations_are_generators():
    q = MSQueue()
    op = q.enqueue("x")
    assert contents(q) == [], "nothing may happen until the scheduler steps the generator"
    run(op)
    assert contents(q) == ["x"]


def test_matches_a_list_alone():
    rng = random.Random(2)
    q, ref = MSQueue(), []
    for i in range(3000):
        if rng.random() < 0.55:
            run(q.enqueue(i))
            ref.append(i)
        else:
            got = run(q.dequeue())
            assert got == (ref.pop(0) if ref else EMPTY)
    assert contents(q) == ref


def test_work_alone_is_constant():
    q = MSQueue()
    for i in range(2000):
        run(q.enqueue(i))
    AtomicRef.reset_counts()
    run(q.enqueue("new"))
    assert (AtomicRef.cas_ok, AtomicRef.cas_failed) == (2, 0), \
        f"an enqueue alone did {AtomicRef.cas_ok} successful and {AtomicRef.cas_failed} failed CAS (want 2 and 0: link, then swing tail)"
    assert AtomicRef.loads <= 4, f"an enqueue on a 2,000-item queue did {AtomicRef.loads:,} loads: use the tail, don't walk the list"
    AtomicRef.reset_counts()
    assert run(q.dequeue()) == 0
    assert (AtomicRef.cas_ok, AtomicRef.cas_failed) == (1, 0), "a dequeue alone is one CAS on head"
    assert AtomicRef.loads <= 4


# ---- A scheduler for simulated threads -----------------------------------------
def simulate(q, threads, rng, max_steps=200_000):
    """threads: list of op lists, each op ("enq", value) or ("deq", None).
    At every step, pick a random thread that still has work and advance its
    current operation by one yield. Returns records
    (thread, kind, value_or_result, start_step, end_step)."""
    todo = [list(ops) for ops in threads]
    cur = [None] * len(threads)
    records, step = [], 0
    while True:
        live = [i for i in range(len(threads)) if cur[i] or todo[i]]
        if not live:
            return records
        i = rng.choice(live)
        if cur[i] is None:
            kind, arg = todo[i].pop(0)
            gen = q.enqueue(arg) if kind == "enq" else q.dequeue()
            cur[i] = [kind, arg, gen, step]
        kind, arg, gen, start = cur[i]
        try:
            next(gen)
        except StopIteration as done:
            records.append((i, kind, arg if kind == "enq" else done.value, start, step))
            cur[i] = None
        step += 1
        assert step <= max_steps, "the simulation ran too long: is some thread spinning?"


def check_history(q, records, producers):
    """Every value once; FIFO per producer; EMPTY only when it could be empty."""
    enq = {v: (s, e) for _, kind, v, s, e in records if kind == "enq"}
    deqs = [(v, s, e) for _, kind, v, s, e in records if kind == "deq"]
    got = [v for v, _, _ in deqs if v is not EMPTY]
    rest = drain(q)
    everything = got + rest
    assert sorted(everything) == sorted(enq), "values lost or duplicated"
    assert len(set(everything)) == len(everything), "a value came out twice"
    when = {v: (s, e) for v, s, e in deqs if v is not EMPTY}
    for p, values in producers.items():
        for a, b in zip(values, values[1:]):  # a was enqueued (and finished) before b started
            if b in when:
                assert a in when, f"{b!r} came out while {a!r}, enqueued earlier by the same producer, stayed in the queue"
                assert not when[b][1] < when[a][0], f"{b!r} was dequeued entirely before {a!r} started: FIFO broken"
    for v, s, e in deqs:
        if v is not EMPTY:
            continue
        for x, (es, ee) in enq.items():
            # x was surely in the queue for the whole dequeue: enqueued before it
            # started, and taken out only after it ended (or never).
            if ee < s and (x not in when or when[x][0] > e):
                raise AssertionError(f"a dequeue returned EMPTY while {x!r} was in the queue the whole time")


@pytest.mark.parametrize("seed", range(40))
def test_random_interleavings(seed):
    rng = random.Random(seed)
    n_prod, n_cons = rng.randint(1, 3), rng.randint(1, 3)
    per = rng.randint(5, 25)
    producers = {p: [f"p{p}-{k}" for k in range(per)] for p in range(n_prod)}
    threads = [[("enq", v) for v in producers[p]] for p in range(n_prod)]
    threads += [[("deq", None)] * rng.randint(per // 2, per + 5) for _ in range(n_cons)]
    rng.shuffle(threads)
    q = MSQueue()
    records = simulate(q, threads, rng)
    check_history(q, records, producers)


def test_single_consumer_sees_each_producer_in_order():
    rng = random.Random(99)
    producers = {p: [(p, k) for k in range(40)] for p in range(4)}
    threads = [[("enq", v) for v in vals] for vals in producers.values()] + [[("deq", None)] * 200]
    q = MSQueue()
    records = simulate(q, threads, rng)
    seen = [v for _, kind, v, _, _ in records if kind == "deq" and v is not EMPTY] + drain(q)
    for p in producers:
        assert [k for (pp, k) in seen if pp == p] == list(range(40)), f"producer {p}'s items came out of order"


# ---- Lock-freedom: pause a thread forever, everyone else must finish ------------------
def pause_at(op, k):
    """Step op k times. Returns True if it is still mid-way (paused), False if it finished."""
    for _ in range(k):
        try:
            next(op)
        except StopIteration:
            return False
    return True


def test_a_paused_enqueue_never_blocks_others():
    paused_somewhere = 0
    for k in range(1, 40):
        q = MSQueue()
        run(q.enqueue("a"))
        run(q.enqueue("b"))
        frozen = q.enqueue("F")
        if not pause_at(frozen, k):
            break
        paused_somewhere += 1
        run_alone(q.enqueue("x"), f"enqueue (with another enqueue paused after {k} steps)")
        out = [run_alone(q.dequeue(), f"dequeue (with an enqueue paused after {k} steps)") for _ in range(5)]
        assert out in (["a", "b", "x", EMPTY, EMPTY], ["a", "b", "F", "x", EMPTY]), \
            f"paused after {k} steps, the others saw {out}"
        run(frozen)  # let it finish
        assert sorted(v for v in out + drain(q) if v is not EMPTY) == ["F", "a", "b", "x"]
    assert paused_somewhere >= 3, "enqueue finished in under 3 steps: does it go through AtomicRef with yield from?"


def test_a_paused_dequeue_never_blocks_others():
    paused_somewhere = 0
    for k in range(1, 40):
        q = MSQueue()
        for v in "abc":
            run(q.enqueue(v))
        frozen = q.dequeue()
        if not pause_at(frozen, k):
            break
        paused_somewhere += 1
        others = [run_alone(q.dequeue(), f"dequeue (with another dequeue paused after {k} steps)") for _ in range(2)]
        run_alone(q.enqueue("x"), f"enqueue (with a dequeue paused after {k} steps)")
        mine = run(frozen)
        everything = others + [mine] + drain(q)
        assert sorted(everything) == ["a", "b", "c", "x"], f"paused after {k} steps: {everything}"
        assert others in (["a", "b"], ["b", "c"]), f"paused after {k} steps, the others got {others}"
    assert paused_somewhere >= 3


def test_paused_after_linking_others_help_the_tail():
    q = MSQueue()
    frozen = q.enqueue("F")
    before = AtomicRef.cas_ok
    while AtomicRef.cas_ok == before:  # step until its first successful CAS: the link
        next(frozen)
    assert contents(q) == ["F"], "the first successful CAS of enqueue should link the node"
    for v in "xyz":
        run_alone(q.enqueue(v), "enqueue behind a lagging tail")
    assert contents(q) == ["F", "x", "y", "z"]
    assert q.tail.peek().value == "z"
    run(frozen)  # its tail CAS now fails: someone already helped
    assert contents(q) == ["F", "x", "y", "z"] and q.tail.peek().value == "z"


def test_a_linked_item_can_be_dequeued_before_the_tail_moves():
    q = MSQueue()
    frozen = q.enqueue("F")
    before = AtomicRef.cas_ok
    while AtomicRef.cas_ok == before:  # step until the link CAS; tail still points at the dummy
        next(frozen)
    got = run_alone(q.dequeue(), "dequeue behind a lagging tail")
    assert got == "F", (f"dequeue returned {'EMPTY' if got is EMPTY else repr(got)}: F was linked, so it is in "
                        "the queue. Decide 'empty' from the dummy's next, not from head == tail")
    assert q.tail.peek() is q.head.peek(), (
        "head moved past tail: when tail still points at the dummy, help swing it forward before moving head")
    assert contents(q) == []
    run(frozen)  # its tail CAS fails: the dequeue already helped
    assert q.tail.peek() is q.head.peek() and contents(q) == []
    run(q.enqueue("y"))
    assert run(q.dequeue()) == "y" and run(q.dequeue()) is EMPTY
