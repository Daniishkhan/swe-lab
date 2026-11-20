import math
import random
import signal

import pytest

from bplus_tree import BPlusTree, Disk, Node, PageFull


@pytest.fixture(autouse=True)
def time_limit():
    """Each test takes well under a few seconds when every operation walks one path (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 20 s: is something scanning every page?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def build(keys, max_keys=4, val=lambda k: k):
    disk = Disk(max_keys)
    t = BPlusTree(disk)
    for k in keys:
        t.put(k, val(k))
    return disk, t


def check_shape(disk, t):
    """Walk the pages directly (no counted reads) and check every B+tree rule."""
    m = disk.max_keys
    leaves, depths = [], set()

    def walk(pid, depth, lo, hi, is_root):
        node = disk.pages[pid]
        assert node is not None, f"page {pid} is reachable but was never written"
        assert node.keys == sorted(node.keys), f"page {pid}: keys not sorted: {node.keys}"
        assert len(set(node.keys)) == len(node.keys), f"page {pid}: duplicate keys {node.keys}"
        if not is_root:
            assert len(node.keys) >= m // 2, f"page {pid} has {len(node.keys)} keys: every node but the root must be at least half full ({m // 2})"
        for k in node.keys:
            assert (lo is None or not k < lo) and (hi is None or k < hi), f"page {pid}: key {k!r} is outside its parent's separators [{lo!r}, {hi!r})"
        if node.leaf:
            depths.add(depth)
            leaves.append(pid)
            return
        assert node.keys, f"internal page {pid} has no keys"
        bounds = [lo] + node.keys + [hi]
        for i, child in enumerate(node.vals):
            walk(child, depth + 1, bounds[i], bounds[i + 1], False)

    walk(t.root, 1, None, None, True)
    assert len(depths) == 1, f"leaves at different depths {sorted(depths)}: the tree must grow at the root"
    assert depths.pop() == t.height()
    for a, b in zip(leaves, leaves[1:]):
        assert disk.pages[a].next == b, f"leaf {a}.next is {disk.pages[a].next}, but the next leaf is {b}"
    assert disk.pages[leaves[-1]].next is None, "the last leaf's next must be None"
    return [k for pid in leaves for k in disk.pages[pid].keys]


def height_bound(n, m):
    """Most levels n keys can need when every node is at least half full."""
    leaves = max(1, math.ceil(n / (m // 2)))
    return 1 + max(0, math.ceil(math.log(leaves, m // 2 + 1) - 1e-9))


# ---- correctness ----
def test_example():
    _, t = build([10, 20, 5, 6, 12, 30, 7, 17], max_keys=3, val=str)
    assert t.get(6) == "6"
    assert t.get(99) is None
    assert t.get(99, "none") == "none"
    assert list(t.range(6, 17)) == [(6, "6"), (7, "7"), (10, "10"), (12, "12")]
    assert t.height() == 2


def test_empty_and_one_key():
    disk, t = build([])
    assert t.get(1) is None and list(t.range(0, 100)) == [] and t.height() == 1
    t.put(5, "five")
    assert t.get(5) == "five" and list(t.range(5, 6)) == [(5, "five")]
    assert list(t.range(6, 100)) == [] and list(t.range(0, 5)) == []
    assert list(t.range(9, 1)) == []


def test_put_replaces():
    disk, t = build(range(50), max_keys=3)
    for k in range(0, 50, 3):
        t.put(k, -k)
    assert [t.get(k) for k in range(50)] == [(-k if k % 3 == 0 else k) for k in range(50)]
    assert [k for k, _ in t.range(0, 50)] == list(range(50)), "replacing a value must not add a second copy of the key"
    assert check_shape(disk, t) == list(range(50))


@pytest.mark.parametrize("m", [3, 4, 5, 8])
def test_random_against_a_dict(m):
    rng = random.Random(m)
    disk, t = Disk(m), None
    t = BPlusTree(disk)
    ref = {}
    for _ in range(3000):
        k, v = rng.randrange(800), rng.random()
        t.put(k, v)
        ref[k] = v
    for k in range(-5, 805):
        assert t.get(k) == ref.get(k)
    keys = sorted(ref)
    for _ in range(200):
        lo, hi = sorted((rng.randrange(-10, 810), rng.randrange(-10, 810)))
        assert list(t.range(lo, hi)) == [(k, ref[k]) for k in keys if lo <= k < hi]
    assert check_shape(disk, t) == keys


@pytest.mark.parametrize("order", ["rising", "falling", "random"])
def test_shape_for_every_insert_order(order):
    n, m = 2000, 4
    keys = list(range(n))
    if order == "falling":
        keys.reverse()
    if order == "random":
        random.Random(2).shuffle(keys)
    disk, t = build(keys, max_keys=m)
    assert check_shape(disk, t) == list(range(n))
    assert t.height() <= height_bound(n, m)


def test_strings():
    words = "the quick brown fox jumps over the lazy dog and keeps on running far away".split()
    disk, t = build(words, max_keys=3, val=len)
    assert list(t.range("d", "p")) == [(w, len(w)) for w in sorted(set(words)) if "d" <= w < "p"]
    assert check_shape(disk, t) == sorted(set(words))


def test_nodes_fit_in_pages():
    disk = Disk(3)
    with pytest.raises(PageFull):
        disk.write(disk.alloc(), Node(True, [1, 2, 3, 4], [1, 2, 3, 4]))
    _, t = build(range(100), max_keys=3)  # Disk refuses any page over 3 keys


# ---- work: pages read and written ----
@pytest.fixture(scope="module")
def big():
    n, m = 20_000, 16
    keys = random.Random(1).sample(range(10 * n), n)
    disk = Disk(m)
    t = BPlusTree(disk)
    disk.reads = disk.writes = 0
    for k in keys:
        t.put(k, k)
    return disk, t, keys, disk.reads, disk.writes


def test_height_is_logarithmic(big):
    disk, t, keys, _, _ = big
    assert t.height() <= height_bound(len(keys), disk.max_keys), f"height {t.height()} for {len(keys):,} keys with {disk.max_keys} keys per page"


def test_get_reads_one_page_per_level(big):
    disk, t, keys, _, _ = big
    h = t.height()
    rng = random.Random(3)
    present = set(keys)
    for k in rng.sample(keys, 500) + [-1, 10 ** 9, 7.5]:
        disk.reads = 0
        assert t.get(k) == (k if k in present else None)
        assert disk.reads <= h, f"get({k}) read {disk.reads} pages, but the tree has {h} levels"


def test_put_writes_only_what_changes(big):
    disk, t, keys, reads, writes = big
    n, h = len(keys), t.height()
    assert writes <= 1.5 * n, f"{writes:,} page writes for {n:,} puts ({writes / n:.2f} each): write a page only when it changed"
    assert reads <= h * n, f"{reads:,} page reads for {n:,} puts: one path down is {h} pages"
    for k in random.Random(4).sample(range(10 * n, 20 * n), 200):  # a few more, one at a time
        h = t.height()  # height() reads pages too, so ask before counting
        disk.reads = disk.writes = 0
        t.put(k, k)
        assert disk.reads <= h, f"put({k}) read {disk.reads} pages (height {h}): one path down"
        # Two pages per level that splits, plus a new root if the root splits.
        assert disk.writes <= 2 * h + 1, f"put({k}) wrote {disk.writes} pages (height {h})"


def test_range_reads_only_the_leaves_it_covers(big):
    disk, t, keys, _, _ = big
    s, m, h = sorted(keys), disk.max_keys, t.height()
    for start in (100, 9_000, 18_500):
        lo, hi = s[start], s[start + 1000]
        disk.reads = 0
        got = list(t.range(lo, hi))
        assert [k for k, _ in got] == s[start:start + 1000]
        budget = h + math.ceil(1000 / (m // 2)) + 2
        assert disk.reads <= budget, f"range over 1,000 keys read {disk.reads} pages (budget {budget}): go down once, then follow next"


def test_range_is_lazy(big):
    disk, t, keys, _, _ = big
    s, h = sorted(keys), t.height()
    disk.reads = 0
    it = t.range(s[50], s[-1] + 1)
    first = [next(it) for _ in range(5)]
    assert [k for k, _ in first] == s[50:55]
    assert disk.reads <= h + 1, f"taking 5 items read {disk.reads} pages: range must yield as it goes, not collect everything first"


def test_many_rising_keys_quickly():
    n, m = 100_000, 32
    disk, t = build(range(n), max_keys=m)
    assert t.height() <= height_bound(n, m)
    assert t.get(77_777) == 77_777 and t.get(n) is None
    assert [k for k, _ in t.range(n - 3, n + 5)] == [n - 3, n - 2, n - 1]
