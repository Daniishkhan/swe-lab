import threading
import time

import pytest

from bounded_queue import BoundedQueue, QueueClosed


def test_fifo_single_thread_and_validation():
    with pytest.raises(ValueError):
        BoundedQueue(0)
    q = BoundedQueue(3)
    q.put("a")
    q.put("b")
    q.put("c")
    assert len(q) == 3
    assert q.get() == "a"
    assert q.get() == "b"
    q.close()
    # Remaining buffered item is drained before QueueClosed is raised.
    assert q.get() == "c"
    with pytest.raises(QueueClosed):
        q.get()
    with pytest.raises(QueueClosed):
        q.put("d")


def test_backpressure_blocks_producer_until_consumer_reads():
    q = BoundedQueue(2)
    q.put(1)
    q.put(2)
    put_done = threading.Event()

    def producer():
        q.put(3)
        put_done.set()

    t = threading.Thread(target=producer)
    t.start()
    time.sleep(0.05)
    assert not put_done.is_set(), "producer must block while queue is full"
    assert q.get() == 1
    assert put_done.wait(timeout=1.0), "producer did not wake after space freed"
    t.join(timeout=1.0)
    assert q.get() == 2
    assert q.get() == 3


def test_many_producers_many_consumers_no_loss_or_dups():
    q = BoundedQueue(16)
    n_prod, n_cons, per_prod = 8, 8, 250
    received = []
    rec_lock = threading.Lock()

    def producer(pid):
        for i in range(per_prod):
            q.put((pid, i))

    def consumer():
        local = []
        while True:
            try:
                local.append(q.get())
            except QueueClosed:
                break
        with rec_lock:
            received.extend(local)

    consumers = [threading.Thread(target=consumer) for _ in range(n_cons)]
    producers = [threading.Thread(target=producer, args=(p,)) for p in range(n_prod)]
    for t in consumers + producers:
        t.start()
    for t in producers:
        t.join(timeout=5.0)
        assert not t.is_alive(), "producer deadlocked"
    q.close()
    for t in consumers:
        t.join(timeout=5.0)
        assert not t.is_alive(), "consumer hung after close()"

    expected = {(p, i) for p in range(n_prod) for i in range(per_prod)}
    assert len(received) == len(expected)
    assert set(received) == expected


def test_close_wakes_blocked_producers_and_consumers():
    q = BoundedQueue(1)
    q.put("full")
    prod_err = []

    def blocked_producer():
        try:
            q.put("blocked")
        except QueueClosed as e:
            prod_err.append(e)

    tp = threading.Thread(target=blocked_producer)
    tp.start()
    time.sleep(0.05)
    q.close()
    tp.join(timeout=1.0)
    assert not tp.is_alive(), "blocked producer did not wake on close()"
    assert len(prod_err) == 1

    # Also test waking blocked consumers on an empty queue
    q2 = BoundedQueue(2)
    cons_err = []

    def blocked_consumer():
        try:
            q2.get()
        except QueueClosed as e:
            cons_err.append(e)

    cs = [threading.Thread(target=blocked_consumer) for _ in range(4)]
    for c in cs:
        c.start()
    time.sleep(0.05)
    q2.close()
    for c in cs:
        c.join(timeout=1.0)
        assert not c.is_alive(), "blocked consumer did not wake on close()"
    assert len(cons_err) == 4
