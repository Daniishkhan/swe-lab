"""
One pass, best so far: fewest jumps and the gas station loop
Topic: 02.10  |  Priority: P1

Problem
-------
Section 6 of the chapter. Both problems look like they need "try every
start" or "try every jump", and both fall to one left-to-right pass that
keeps one or two running numbers.

1. min_jumps(nums): you stand on index 0. From index i you may jump forward
   to any index from i + 1 up to i + nums[i] (nums[i] >= 0). Return the
   fewest jumps that reach the last index, or -1 if you can't reach it.

       min_jumps([2, 3, 1, 1, 4])  -> 2     # 0 -> 1 -> 4
       min_jumps([2, 3, 0, 1, 4])  -> 2
       min_jumps([3, 2, 1, 0, 4])  -> -1    # everything gets stuck on the 0
       min_jumps([7])              -> 0     # already on the last index

2. circuit_start(gas, cost): n stations on a loop. Station i gives you
   gas[i] liters; driving from station i to station i + 1 (and from the last
   one back to station 0) burns cost[i] liters. The tank starts empty and
   has no limit. Return a station you can start from and drive the whole
   loop once without the tank going below zero, or -1 if there is none.
   If several stations work, any one of them is accepted.

       circuit_start([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])  -> 3
       circuit_start([2, 3, 4], [3, 4, 3])              -> -1
       circuit_start([5], [5])                          -> 0

Requirements
------------
- Don't modify the caller's lists. Both lists have length n >= 1.
- min_jumps: O(n) time, O(1) extra memory.
- circuit_start: O(n) time, O(1) extra memory. That rules out a list of
  running totals: keep the numbers you need in a few variables.

What the tests measure
----------------------
- The lists are wrapped so that every read of an item is counted
  (indexing and iterating both count).
- min_jumps on 30,000 items: at most 3 n reads, and a 2-second cap. The
  table method ("fewest jumps to reach j, for every j, from every i that
  reaches it") is correct but does about n^2 / 2 updates when jumps are
  long, which is far over the cap.
- min_jumps' extra memory, on 200,000 plain-int stones, is measured with
  tracemalloc: under 20 KB. A table or a BFS queue of indices needs
  megabytes.
- circuit_start on 20,000 stations: at most 2 reads per station of each
  list. "Try every start and drive until you run dry" is correct but reads
  about n^2 / 2 items on the test's input, where the only good start is in
  the middle and every other start drives a long way before failing, in
  whatever order you try them.
- circuit_start's extra memory, on 200,000 plain-int stations, is measured
  with tracemalloc: under 20 KB. A prefix-sum list needs megabytes.

Before you code (say it out loud)
---------------------------------
1. min_jumps: think in rounds. Which indices can you reach with 0 jumps,
   with 1 jump, with 2? Why is "the farthest index the current round can
   reach" the only number you need to start the next round?
2. circuit_start: if the total gas is less than the total cost, why is no
   start possible? If it is at least the total cost, why must a start exist?
3. circuit_start: you start at s and run dry just after station i. Why can
   no station between s and i be the answer either? (Hint: you arrived at
   each of them with a tank of zero or more.)

Run:  pytest -k gas_station
"""


def min_jumps(nums: list[int]) -> int:
    raise NotImplementedError


def circuit_start(gas: list[int], cost: list[int]) -> int:
    raise NotImplementedError
