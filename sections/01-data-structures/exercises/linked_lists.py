"""
Linked list moves: reverse, middle, cycle
Topic: 01.02  |  Priority: P0

Problem
-------
Three classic pointer moves from section 5 of the chapter. A node has two
attributes, `val` and `next` (the next node, or None). The tests pass in
their own node class with the same two attributes, so only use `.val` and
`.next`, and don't add attributes to nodes.

    1 -> 2 -> 3 -> None
    reverse(head)   -> the node 3, and the list now reads 3 -> 2 -> 1 -> None
    middle(head)    -> the node 2
    has_cycle(head) -> False

1. reverse(head): reverse the list in place and return the new head. Reuse
   the same node objects (change their `.next`); don't build new nodes.
2. middle(head): return the middle node. With an even number of nodes,
   return the second of the two middles (1 -> 2 -> 3 -> 4 gives node 3).
   Return None for an empty list.
3. has_cycle(head): True if following `.next` from head never reaches None
   (some node points back to an earlier one).

Requirements
------------
- All three in O(n) time and O(1) extra memory: a few variables, no list or
  set of nodes, and no recursion (a 200,000-node list would pass Python's
  recursion limit of about 1,000).
- Empty list (head is None) works for all three.

What the tests measure
----------------------
They count every read of `.next`, measure the memory your call allocates
(tracemalloc), and check that reversal keeps the same node objects. A set of
seen nodes, a list of nodes, or a recursive reverse fails.

Before you code (say it out loud)
---------------------------------
1. In reverse: which pointer must you save before you change cur.next, and
   what is lost if you don't?
2. Why must a fast pointer that moves 2 steps meet a slow one that moves 1
   inside a loop? Why can't it jump over it?
3. Walking the list once to count its length, then again to the middle, is
   also O(n) and O(1) memory. What does the fast/slow version save?

Run:  pytest -k linked_lists
"""

from __future__ import annotations


class Node:
    """A singly linked list node, for your own experiments."""

    def __init__(self, val, next: "Node | None" = None):
        self.val = val
        self.next = next


def reverse(head):
    raise NotImplementedError


def middle(head):
    raise NotImplementedError


def has_cycle(head) -> bool:
    raise NotImplementedError
