"""
Scheduling with exchange arguments: most jobs on time, best weighted order
Topic: 02.10  |  Priority: P1

Problem
-------
Section 5 of the chapter proved "earliest deadline first" with an exchange
argument: swap two neighbors that are in the wrong order and nothing gets
worse. Here you use the same tool on two new problems. One machine runs one
job at a time, starting at time 0, with no gaps and no pausing.

1. most_on_time(jobs): jobs[i] = (duration, deadline), duration >= 1. A job
   is on time if it finishes at or before its deadline. You may skip jobs.
   Return the indices of as many jobs as possible that can ALL be on time,
   listed in an order that runs them all on time.

       most_on_time([(3, 5), (2, 4), (1, 2), (4, 7)])  -> [2, 1, 3]
           # run job 2 (ends 1), job 1 (ends 3), job 3 (ends 7); skip job 0
       most_on_time([(100, 200), (200, 1300), (1000, 1250), (2000, 3200)])
           -> [0, 2, 1]   # (or any other 3 jobs in a working order)
       most_on_time([(5, 3)])  -> []

2. best_weighted_order(jobs): jobs[i] = (duration, weight), both >= 1. Run
   every job. Job i costs weight_i * (its finish time). Return the order
   (a list of all the indices) with the smallest total cost.

       best_weighted_order([(3, 1), (1, 2), (2, 2)])  -> [1, 2, 0]
           # finish times 1, 3, 6: cost 2*1 + 2*3 + 1*6 = 14

   Hint: take two neighbors i then j somewhere in the order. Swapping them
   changes only their own two costs (why?). Work out when the swap helps,
   and you have the sort key. Ties can go either way.

Requirements
------------
- Don't modify the caller's list. Empty input: [] for both.
- Both: O(n log n). For most_on_time: sort once, then use a heap.

What the tests measure
----------------------
Every duration, deadline and weight is wrapped in a number that counts
comparisons. Arithmetic on them (+, -, *, /, unary -) gives another counted
number, so a key you compute from them is counted too.
- most_on_time on 3,000 jobs: under 6 n log2 n comparisons (about
  208,000). Scanning the kept jobs for the longest one every time you must
  drop one needs over a million.
- best_weighted_order on 3,000 jobs: under 3 n log2 n (about 104,000).
  An insertion or selection sort by hand needs millions.
- Optimality: against brute force (every subset, every order) on small
  inputs, and against values computed offline on big ones.

Before you code (say it out loud)
---------------------------------
1. most_on_time: walk the jobs in deadline order, adding each one. When the
   newest one would be late, you must drop one job. Which one, and why does
   dropping it leave you at least as well off as any other choice?
2. Why is deadline order the right order to RUN a set of jobs, if any order
   runs them all on time?
3. best_weighted_order: write the cost of "i then j" and of "j then i".
   What cancels? What's left is the rule.

Run:  pytest -k job_scheduling
"""


def most_on_time(jobs: list[tuple]) -> list[int]:
    raise NotImplementedError


def best_weighted_order(jobs: list[tuple]) -> list[int]:
    raise NotImplementedError
