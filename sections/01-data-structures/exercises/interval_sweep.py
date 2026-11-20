"""
Sweep line: rooms, coverage and point counts
Topic: 01.09  |  Priority: P1

Problem
-------
Sections 5 and 6 of the chapter. An interval is a pair (start, end) with
start < end, half-open: [start, end) contains start but not end. So a
meeting (9, 10) and a meeting (10, 11) can share one room.

1. min_rooms(meetings): the fewest rooms that hold every meeting, which is
   the largest number of meetings going on at the same moment.

       min_rooms([(0, 30), (5, 10), (15, 20)])  -> 2
       min_rooms([(9, 10), (10, 11)])           -> 1

2. covered_at_least(intervals, k): the total length of time during which at
   least k intervals overlap (k >= 1). Times are numbers here.

       covered_at_least([(0, 10), (5, 15), (8, 9)], 2)  -> 5   # [5, 10)
       covered_at_least([(0, 10), (5, 15), (8, 9)], 1)  -> 15  # [0, 15)
       covered_at_least([(0, 10), (5, 15), (8, 9)], 3)  -> 1   # [8, 9)

3. count_at(intervals, times): for each time t in times, how many intervals
   contain t (start <= t < end). Answer in the order the times were given.

       count_at([(1, 5), (2, 3), (4, 8)], [0, 2, 3, 4, 8])  -> [0, 2, 1, 2, 0]

Requirements
------------
- Don't modify the caller's lists. Empty input: 0, 0 and [0, 0, ...].
- min_rooms and count_at: times only need comparisons. covered_at_least
  also subtracts (end - start gives a number).
- min_rooms and covered_at_least: O(n log n). Sort the events once, then
  one sweep.
- count_at: O((n + q) log n) for n intervals and q times. Hint: the count at
  t is (starts <= t) minus (ends <= t).

What the tests measure
----------------------
They wrap every time in an object that counts comparisons:
- min_rooms and covered_at_least on 2,000 intervals: under
  6 n log2 n + 20 n comparisons (about 170,000). Counting, for every
  meeting, how many others are running at its start needs about 8 million.
- count_at with 2,000 intervals and 2,000 times: under
  6 (n + q) log2 (n + q) + 10 (n + q) comparisons (about 330,000). Checking
  every interval for every time needs about 8 million.

Before you code (say it out loud)
---------------------------------
1. What are the events, and what does the counter mean between two events?
2. Two events at the same time, an end and a start: which goes first, and
   what answer do you get for [(9, 10), (10, 11)] if you get it backwards?
3. covered_at_least: between two neighboring event times the count can't
   change. What do you add to the total for that stretch?

Run:  pytest -k interval_sweep
"""


def min_rooms(meetings: list[tuple]) -> int:
    raise NotImplementedError


def covered_at_least(intervals: list[tuple], k: int):
    raise NotImplementedError


def count_at(intervals: list[tuple], times: list) -> list[int]:
    raise NotImplementedError
