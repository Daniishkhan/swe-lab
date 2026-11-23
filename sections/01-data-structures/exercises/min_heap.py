"""
Binary min-heap from scratch
Topic: 01.04  |  Priority: P0

Problem
-------
Build sections 3 to 5 of the chapter: a min-heap stored in a plain Python
list, where the children of index i are 2i + 1 and 2i + 2 and its parent is
(i - 1) // 2.

    h = MinHeap()
    for x in [5, 3, 8, 1]:
        h.push(x)
    h.peek() -> 1,  len(h) -> 4
    h.pop()  -> 1,  h.pop() -> 3

    MinHeap.from_list([9, 4, 7, 1]).pop() -> 1

Requirements
------------
- push(x): O(log n). pop(): remove and return the smallest, O(log n).
  peek(): the smallest without removing it, O(1). len(h).
- pop() and peek() on an empty heap raise IndexError.
- MinHeap.from_list(items): build a heap from any iterable in O(n) with
  bottom-up heapify. Don't modify the caller's list.
- Items only need `<` (they may not be numbers). Equal items are fine.
- No heapq, sorted() or list.sort() inside: the heap must do its own work.

What the tests measure
----------------------
They use items that count every comparison (<, <=, >, >=):
- pushing 4,096 falling values (each new one is the smallest so far) must
  cost about n log2 n comparisons, not n^2;
- popping all of them must cost about 2 n log2 n, so a pop that scans for
  the minimum fails;
- from_list on 32,768 items, random or falling, must use fewer than 3n
  comparisons, so building by n pushes or by sorting fails.

Before you code (say it out loud)
---------------------------------
1. Where are the children of index i? The parent?
2. In sift-down, why swap with the smaller child?
3. Why is bottom-up heapify O(n)? (Hint: count how far nodes at each
   height can move, and how many nodes there are at that height.)
4. Why does pop move the *last* item to the root, and not, say, a child?

Run:  pytest -k min_heap
"""


class MinHeap:
    def __init__(self):
        raise NotImplementedError

    @classmethod
    def from_list(cls, items) -> "MinHeap":
        raise NotImplementedError

    def push(self, x) -> None:
        raise NotImplementedError

    def pop(self):
        raise NotImplementedError

    def peek(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
