"""
Python foundations: control flow, loops, functions & built-in data structures
Topic: 10.14  |  Also: 10.13  |  Priority: P0
Chapters: sections/10-code-quality-design-testing/concepts/python-control-flow.html, sections/10-code-quality-design-testing/concepts/python-data-structures.html

Five interview-essential Python foundations drills covering reverse range,
early-return 2D search, O(n) set-backed deduplication, dictionary bucketing,
and set algebra.

Functions
---------
countdown_evens(n) -> list[int]
    Return all even integers from n down to 0 inclusive, in descending order.
    If n is odd, start at n - 1. Raise ValueError if n < 0.
    countdown_evens(6) == [6, 4, 2, 0]
    countdown_evens(5) == [4, 2, 0]
    countdown_evens(0) == [0]

first_negative_coords(grid) -> tuple[int, int] | None
    Scan a 2D list of ints row by row, left to right (rows may have different
    lengths or be empty). Return (row_index, col_index) of the first element
    strictly less than 0, or None if no negative number exists.
    first_negative_coords([[1, 2], [0, -5, -1]]) == (1, 1)

dedupe_preserve_order(items) -> list
    items is any iterable of hashable values (list, tuple, generator, etc.).
    Return a new list containing each unique value once, in the order it first
    appeared. Do not mutate items if a list is passed.
    Target: O(n) average time using a helper set (NOT O(n^2) `if x not in out`).
    dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

word_positions(text) -> dict[str, list[int]]
    Split text on whitespace and normalize each word to lowercase. Return a
    dict mapping each distinct word to the ascending list of 0-based token
    indices where it appears. Empty or whitespace-only text returns {}.
    Target: O(n) time in one pass over the tokens.
    word_positions("Go dog go") == {"go": [0, 2], "dog": [1]}

tag_diff(current, target) -> tuple[list, list, list]
    current and target are iterables of comparable, hashable tags (may contain
    duplicates or be single-use generators). Return a 3-tuple of sorted lists:
      (to_add, to_remove, kept)
      - to_add:    tags in target but not in current
      - to_remove: tags in current but not in target
      - kept:      tags present in both current and target
    Target: O(n + m + k log k) using set algebra (& and -), NOT O(n * m) scans.
    tag_diff(["a", "b", "c"], ["b", "c", "d"]) == (["d"], ["a"], ["b", "c"])

Before you code (say it out loud)
---------------------------------
1. Why does `range(n, 0, -2)` fail `countdown_evens(6)`, and what stop value
   fixes it?
2. Why is extracting a helper function with `return (r, c)` cleaner than using
   `break` inside a nested 2D loop?
3. Why does `dedupe_preserve_order` pair a `set` with a `list` instead of using
   only a `list` or only a `set`?

Run:  python3 -m pytest -k py_foundations
"""


def countdown_evens(n):
    raise NotImplementedError


def first_negative_coords(grid):
    raise NotImplementedError


def dedupe_preserve_order(items):
    raise NotImplementedError


def word_positions(text):
    raise NotImplementedError


def tag_diff(current, target):
    raise NotImplementedError
