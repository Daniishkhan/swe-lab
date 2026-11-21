"""
Delta debugging: shrink a failing input until every piece matters
Topic: 13.06  |  Priority: P0

Problem
-------
Section 7 of the chapter. A bug shows up on a big input: 2 million log
lines, a 40 KB JSON file, a list of 1,000 operations. Find a small piece of
it that still shows the bug, without reading it yourself, by running the
test again and again on smaller and smaller pieces.

    fails = lambda sub: 3 in sub and 12 in sub     # the bug needs 3 and 12 together
    shrink(list(range(16)), fails)                  -> [3, 12]

shrink(items, fails) -> list
  - items is a list; values may repeat. fails(sub) returns True when the bug
    shows up on the list sub, and False when it doesn't.
  - You may assume fails(items) is True and fails([]) is False.
  - Return a sub-list of items (some of its items, in their original order)
    that still fails and is 1-minimal: removing any single item from it
    makes fails return False.
  - Remove items by position, never by value: values can repeat, and a bug
    can need two copies of the same value.
  - Don't change the list you were given.
  - fails can be any function. It doesn't have to be monotone (monotone:
    adding items to a failing list never makes it pass). When it isn't,
    removing one item can free another item that couldn't go before. So
    after any pass over single items that removes something, make another,
    until a whole pass removes nothing.

What the tests measure
----------------------
- Calls to fails, counted. In real life each call is one run of the
  program, which can take seconds, so the number of calls is the cost.
  * 4,000 items, the bug needs 1 of them: at most 100 calls.
  * 4,000 items, the bug needs 2 of them together, in many placements (both
    in one half, one in each half, at the very ends): at most 600 calls.
  * 4,000 items, the bug needs 3 of them: at most 1,000 calls.
  Removing one item at a time costs about 4,000 calls, so it fails.
- Target: O(k log n) calls when the bug needs k of the n items. Cutting out
  halves, then quarters, and so on (section 7) takes about 2k * log2(n/k)
  calls: 24 for k = 1, 62 for k = 3. On the 4,000-item tests, four ways of
  writing that halving took between 7 and 85 calls, and Zeller's classic
  ddmin took up to about 300. Small details move the count (whether you
  skip trying an empty list, how you split an odd length), so any count
  inside the budget is fine.
- 1-minimality is checked on every answer, with calls that aren't counted.
- Repeated values, a bug that needs three copies of one value, order kept
  (also on a reversed input), and three bugs that aren't monotone: an odd
  number of quote marks; "an x plus more ( than )", where removing a )
  lets a ( go that couldn't go before (run on all 1,219 failing strings of
  up to 7 characters over "()x"); and a chain in "aaabbc" with more a than
  b and more b than c, where cutting the c frees a b, and cutting that b
  frees an a, so two passes over the single items aren't enough.

Before you code (say it out loud)
---------------------------------
1. You cut out the first half and the bug is gone. You put it back, cut out
   the second half, and the bug is gone again. What does that tell you,
   and what do you try next?
2. Removing one item at a time is correct. Why is it still the wrong tool?
   How many runs is it on 2 million lines, at 2 seconds a run?
3. When can you stop, and how do you know the result is 1-minimal?
4. 1-minimal isn't "the smallest failing input there is". Why not, and why
   is that one too expensive to find?

Run:  pytest -k delta_debug
"""


def shrink(items, fails):
    raise NotImplementedError
