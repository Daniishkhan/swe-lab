r"""
Tree traversals, BST validation and building a balanced tree
Topic: 01.03  |  Priority: P0

Problem
-------
Section 7 of the chapter, plus two classic tree questions. Trees are made
of TreeNode objects (below): `val`, `left`, `right`.

        8
       / \
      3   10          preorder    -> [8, 3, 1, 6, 10]
     / \                inorder     -> [1, 3, 6, 8, 10]
    1   6               postorder   -> [1, 6, 3, 10, 8]
                        level_order -> [[8], [3, 10], [1, 6]]

1. preorder(root), inorder(root), postorder(root): lists of values.
2. level_order(root): a list of levels, each a list of values left to right.
3. is_valid_bst(root): True if every node's value is strictly greater than
   everything in its left subtree and strictly less than everything in its
   right subtree. Equal values are not allowed. An empty tree is valid.
4. build_balanced(vals): vals is sorted and has no duplicates. Return the
   root of a BST holding exactly those values with the smallest possible
   height (for n values, the number of levels is the bit length of n).

Requirements
------------
- Every function takes empty input (None, or []) and returns [] / True /
  None as fits.
- No recursion in 1 to 3: the tests use a 100,000-node chain, far past
  Python's recursion limit of about 1,000. Keep your own stack or queue.
  build_balanced may recurse: its depth is only about log2 n.
- All O(n) time. level_order must not shift a list (no pop(0)).
- build_balanced reads each input value once: no slicing at every level
  (that copies O(n log n) items).

What the tests measure
----------------------
100,000-node chains (recursion fails), a 524,287-node tree with a time cap
(pop(0) on a long queue fails), a validity check on a 100,000-node chain
with a time cap (re-scanning subtrees is O(n^2)), and an input list that
counts reads for build_balanced
(slices of it count too). Copying it once and slicing the copy would dodge
the counter: don't. Pass indexes (lo, hi) instead.

Before you code (say it out loud)
---------------------------------
1. For each order, at which of the three "finger passes" is the node visited?
2. Iterative in-order: why go left as far as possible before visiting?
3. Post-order without recursion: one trick is to produce node, right, left
   and reverse it at the end. Why does that work?
4. is_valid_bst: why is comparing each node with its children not enough?
   What range must each node's value fall in?

Run:  pytest -k tree_traversals
"""

from __future__ import annotations


class TreeNode:
    def __init__(self, val, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def preorder(root: TreeNode | None) -> list:
    raise NotImplementedError


def inorder(root: TreeNode | None) -> list:
    raise NotImplementedError


def postorder(root: TreeNode | None) -> list:
    raise NotImplementedError


def level_order(root: TreeNode | None) -> list[list]:
    raise NotImplementedError


def is_valid_bst(root: TreeNode | None) -> bool:
    raise NotImplementedError


def build_balanced(vals: list) -> TreeNode | None:
    raise NotImplementedError
