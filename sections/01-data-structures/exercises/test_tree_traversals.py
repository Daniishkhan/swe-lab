import random
import signal
import time
from bisect import bisect_left, bisect_right
from collections.abc import Sequence

import pytest

from tree_traversals import TreeNode, build_balanced, inorder, is_valid_bst, level_order, postorder, preorder


@pytest.fixture(autouse=True)
def time_limit():
    """O(n) code runs each test in about a second at most. Shifting a long
    queue with pop(0), or re-scanning subtrees, takes far longer, so 5 s is
    a generous line (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 5 s: pop(0) on a long list, or re-walking subtrees for every node?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(5)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def bst_from(keys):
    """Insert keys into a BST. Records each key's depth and the open range
    (lo, hi) its subtree covers, so tests can predict every order without
    walking the tree."""
    root, info, made = None, {}, []
    for k in keys:
        if root is None:
            root = TreeNode(k)
            info[k] = (0, None, None)
            made.append(root)
            continue
        n, d, lo, hi = root, 0, None, None
        while True:
            d += 1
            if k < n.val:
                hi = n.val
                if n.left is None:
                    n.left = TreeNode(k)
                    made.append(n.left)
                    break
                n = n.left
            else:
                lo = n.val
                if n.right is None:
                    n.right = TreeNode(k)
                    made.append(n.right)
                    break
                n = n.right
        info[k] = (d, lo, hi)
    return root, info, made


def subtree(keys_sorted, lo, hi):
    a = 0 if lo is None else bisect_right(keys_sorted, lo)
    b = len(keys_sorted) if hi is None else bisect_left(keys_sorted, hi)
    return keys_sorted[a:b]


def check_block(block, v, node_first):
    """A subtree's block: the node first (pre) or last (post), and the rest
    is all of its left subtree, then all of its right subtree."""
    rest = block[1:] if node_first else block[:-1]
    assert (block[0] if node_first else block[-1]) == v
    split = sum(1 for x in rest if x < v)
    assert all(x < v for x in rest[:split]) and all(x > v for x in rest[split:]), f"left and right subtrees of {v} are mixed"


def check_orders(keys):
    root, info, _ = bst_from(keys)
    ks = sorted(keys)
    assert inorder(root) == ks
    pre, post = preorder(root), postorder(root)
    assert sorted(pre) == ks and sorted(post) == ks
    pos_pre = {v: i for i, v in enumerate(pre)}
    pos_post = {v: i for i, v in enumerate(post)}
    for v, (d, lo, hi) in info.items():
        sub = subtree(ks, lo, hi)
        i = pos_pre[v]
        assert sorted(pre[i:i + len(sub)]) == sub, f"pre-order: {v}'s subtree is not right after it"
        check_block(pre[i:i + len(sub)], v, node_first=True)
        j = pos_post[v]
        assert sorted(post[j - len(sub) + 1:j + 1]) == sub, f"post-order: {v}'s subtree is not right before it"
        check_block(post[j - len(sub) + 1:j + 1], v, node_first=False)
    depth = max(d for d, _, _ in info.values()) + 1 if info else 0
    levels = [sorted(v for v, (d, _, _) in info.items() if d == lvl) for lvl in range(depth)]
    assert level_order(root) == levels


def chain(n, side):
    """A 'left' chain is n-1 -> n-2 -> ... -> 0 down left children; a
    'right' chain is 0 -> 1 -> ... -> n-1 down right children. Both are
    valid BSTs of height n."""
    nodes = [TreeNode(i) for i in range(n)]
    for i in range(n - 1):
        if side == "left":
            nodes[i + 1].left = nodes[i]
        else:
            nodes[i].right = nodes[i + 1]
    return nodes[-1] if side == "left" else nodes[0], nodes


# Traversals
def test_example():
    root = TreeNode(8, TreeNode(3, TreeNode(1), TreeNode(6)), TreeNode(10))
    assert preorder(root) == [8, 3, 1, 6, 10]
    assert inorder(root) == [1, 3, 6, 8, 10]
    assert postorder(root) == [1, 6, 3, 10, 8]
    assert level_order(root) == [[8], [3, 10], [1, 6]]


def test_empty_and_single():
    for f in (preorder, inorder, postorder, level_order):
        assert f(None) == []
    one = TreeNode("x")
    assert preorder(one) == inorder(one) == postorder(one) == ["x"]
    assert level_order(one) == [["x"]]


def test_warmup_tree():
    check_orders([8, 3, 10, 1, 6, 14, 4, 7, 13])
    root = bst_from([8, 3, 10, 1, 6, 14, 4, 7, 13])[0]
    assert preorder(root) == [8, 3, 1, 6, 4, 7, 10, 14, 13]
    assert postorder(root) == [1, 4, 7, 6, 3, 13, 14, 10, 8]
    assert level_order(root) == [[8], [3, 10], [1, 6, 14], [4, 7, 13]]


def test_non_bst_with_duplicates():
    # Non-BST with duplicate values: catches inorder() cheating via sorted(preorder(root)).
    root = TreeNode(1, TreeNode(5, TreeNode(2), TreeNode(5)), TreeNode(0, TreeNode(9)))
    assert preorder(root) == [1, 5, 2, 5, 0, 9]
    assert inorder(root) == [2, 5, 5, 1, 9, 0]
    assert postorder(root) == [2, 5, 5, 9, 0, 1]
    assert level_order(root) == [[1], [5, 0], [2, 5, 9]]


def test_random_shapes():
    rng = random.Random(17)
    for _ in range(150):
        check_orders(rng.sample(range(500), rng.randint(1, 60)))


@pytest.mark.parametrize("side", ["left", "right"])
def test_deep_chain_without_recursion(side):
    n = 100_000
    root, _ = chain(n, side)
    up, down = list(range(n)), list(range(n - 1, -1, -1))
    assert inorder(root) == up
    assert preorder(root) == (down if side == "left" else up)
    assert postorder(root) == (up if side == "left" else down)
    levels = level_order(root)
    assert len(levels) == n and levels[0] == [n - 1 if side == "left" else 0] and levels[-1] == [0 if side == "left" else n - 1]


def test_level_order_on_a_wide_tree():
    n = 2 ** 19 - 1  # 524,287 nodes, 19 levels; the last level alone has 262,144
    nodes = [TreeNode(i) for i in range(n)]
    for i in range((n - 1) // 2):
        nodes[i].left, nodes[i].right = nodes[2 * i + 1], nodes[2 * i + 2]
    start = time.perf_counter()
    levels = level_order(nodes[0])
    took = time.perf_counter() - start
    assert took < 4.0, f"level_order took {took:.1f} s on {n:,} nodes (an O(n) deque version finishes in ~1 s): is the queue a list with pop(0)?"
    assert len(levels) == 19
    for d, level in enumerate(levels):
        assert level == list(range(2 ** d - 1, 2 ** (d + 1) - 1)), f"level {d} is wrong"


# is_valid_bst
def test_valid_bst_small():
    assert is_valid_bst(None) is True
    assert is_valid_bst(TreeNode(1)) is True
    assert is_valid_bst(bst_from([8, 3, 10, 1, 6, 14, 4, 7, 13])[0]) is True
    assert is_valid_bst(TreeNode(2, TreeNode(1), TreeNode(3))) is True
    assert is_valid_bst(TreeNode(2, TreeNode(3), TreeNode(1))) is False
    assert is_valid_bst(TreeNode(2, TreeNode(2))) is False  # equal values aren't allowed
    assert is_valid_bst(TreeNode(2, None, TreeNode(2))) is False
    assert is_valid_bst(TreeNode(0, TreeNode(-5), TreeNode(5))) is True
    assert is_valid_bst(TreeNode(0, None, TreeNode(-1))) is False  # 0 is a real lo bound, not "nothing yet"
    assert is_valid_bst(TreeNode(0, None, TreeNode(0))) is False
    assert is_valid_bst(TreeNode(0, TreeNode(1), None)) is False  # 0 is a real hi bound, not "nothing yet"
    assert is_valid_bst(TreeNode(0, TreeNode(0), None)) is False


def test_valid_bst_checks_the_whole_subtree():
    # The chapter's trap: every parent/child pair is fine, but 45 is in 40's left subtree.
    assert is_valid_bst(TreeNode(40, TreeNode(20, None, TreeNode(45)), TreeNode(60))) is False
    # The same trap on the right side: 5 is in 10's right subtree.
    assert is_valid_bst(TreeNode(10, TreeNode(5), TreeNode(15, TreeNode(5)))) is False
    # Two levels up: 35 must be > 30 (its parent's left limit) and < 40 (the root).
    assert is_valid_bst(TreeNode(40, TreeNode(30, None, TreeNode(35, None, TreeNode(41))), TreeNode(50))) is False
    assert is_valid_bst(TreeNode(40, TreeNode(30, None, TreeNode(35, None, TreeNode(39))), TreeNode(50))) is True


def test_valid_bst_random():
    rng = random.Random(23)
    for _ in range(200):
        keys = rng.sample(range(100), rng.randint(2, 30))
        root, _, nodes = bst_from(keys)
        assert is_valid_bst(root) is True
        # Swap two values: the tree is no longer sorted in-order, so it's invalid.
        a, b = rng.sample(nodes, 2)
        a.val, b.val = b.val, a.val
        assert is_valid_bst(root) is False


@pytest.mark.parametrize("side", ["left", "right"])
def test_valid_bst_deep_chain(side):
    n = 100_000
    root, nodes = chain(n, side)
    assert is_valid_bst(root) is True
    if side == "left":
        nodes[0].right = TreeNode(n + 5)  # bigger than its parent, 0, but also bigger than the root
        assert is_valid_bst(root) is False
        nodes[0].right = TreeNode(0.5)  # between 0 and 1: valid
        assert is_valid_bst(root) is True
    else:
        nodes[-1].left = TreeNode(-5)  # smaller than its parent, n-1, but also smaller than the root
        assert is_valid_bst(root) is False
        nodes[-1].left = TreeNode(n - 1.5)  # between n-2 and n-1: valid
        assert is_valid_bst(root) is True


# build_balanced
class TooManyReads(AssertionError):
    pass


class CountingList(Sequence):
    def __init__(self, items, budget):
        self._items, self.reads, self.budget = list(items), 0, budget

    def _tick(self, k=1):
        self.reads += k
        if self.reads > self.budget:
            raise TooManyReads(f"over {self.budget:,} reads of a {len(self._items):,}-item list: is something slicing at every level?")

    def __getitem__(self, i):
        if isinstance(i, slice):  # a slice is a counting list too, sharing the same tally
            out = CountingList.__new__(CountingList)
            out._items, out.budget, out._root = self._items[i], self.budget, getattr(self, "_root", self)
            out._root._tick(len(out._items))
            return out
        getattr(self, "_root", self)._tick()
        return self._items[i]

    def __iter__(self):
        for x in self._items:
            getattr(self, "_root", self)._tick()
            yield x

    def __len__(self):
        return len(self._items)


def count_nodes(n):  # recursion is fine here: only called once depths are checked
    return 0 if n is None else 1 + count_nodes(n.left) + count_nodes(n.right)


def check_balanced(root, vals):
    best = len(vals).bit_length()
    for v in vals:  # find every value by BST search, at most `best` levels down
        n, d = root, 1
        while n is not None and n.val != v:
            n, d = (n.left if v < n.val else n.right), d + 1
        assert n is not None, f"{v} can't be found by searching: not a valid BST, or missing"
        assert d <= best, f"{v} is at level {d}, but {len(vals)} values fit in {best} levels"
    assert count_nodes(root) == len(vals), "the tree has extra nodes"


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 7, 10, 100])
def test_build_balanced_small(n):
    vals = [3 * i - 50 for i in range(n)]
    root = build_balanced(vals)
    if n == 0:
        assert root is None
    else:
        check_balanced(root, vals)


@pytest.mark.parametrize("n", [100_000, 2 ** 17 - 1])
def test_build_balanced_reads_each_value_once(n):
    vals = list(range(0, 2 * n, 2))
    root = build_balanced(CountingList(vals, budget=2 * n))
    check_balanced(root, vals)
