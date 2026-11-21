"""
Differential testing: the smallest input where two versions disagree
Topic: 13.06  |  Priority: P0

Problem
-------
Section 5 of the chapter. You have a fast candidate (say, the version an
assistant wrote) and a slow oracle that is obviously correct. Run both on
every small input, smallest first, and report the first input where they
disagree. You don't need to know the right answer to find the bug: two
answers that must agree, don't. And the smallest such input is the easiest
one to understand, and the best regression test.

The tests use a toy problem: the most common value in a list, ties going to
the smallest value, None for an empty list.

    def candidate(xs):                       # an assistant's version
        return Counter(xs).most_common(1)[0][0]

    find_counterexample(candidate, oracle, [1, 2, 3], 4)   -> []
    # [] is tried first, and candidate crashes on it. That counts.

find_counterexample(candidate, oracle, alphabet, max_len) -> list or None
  - Try every list whose items come from alphabet: length 0, then 1, then 2,
    and so on up to max_len. Within one length, go in the order
    itertools.product(alphabet, repeat=length) gives them (by the order of
    alphabet, position by position).
  - Return the first list x (as a list) on which the two disagree:
      * candidate(x) != oracle(x), or
      * candidate raises an exception, or
      * candidate changes the list it was given.
    Return None if they agree on every list up to max_len.
  - Call each function with its own fresh copy of x (a list, as its real
    callers would pass), so that neither can change what the other sees.
    The oracle never raises and never changes its input.

What the tests measure
----------------------
- Calls to candidate and to oracle, counted. Stop at the first disagreement:
  each may be called at most 3 times per list you try. Trying every list up
  to max_len and then picking the smallest fails: with alphabet [1, 2, 3]
  and max_len 6 that's 1,093 lists, against a first disagreement at list 24.
- Five plausible-but-wrong versions of the toy problem, one that raises on
  a 3, and a correct one that must come back None. Each wrong one has a
  smallest counterexample worked out by hand.
- The order of alphabet decides which counterexample comes first.

Before you code (say it out loud)
---------------------------------
1. Why smallest first? Would you rather paste a 2-item list or a 40-item one
   into a bug report, or into a prompt for the assistant?
2. A candidate sorts its input in place and then answers correctly. Why is
   that still a bug, and how do you notice it?
3. A candidate crashes on []. Is that a disagreement? What does the oracle
   say about []?
4. How many lists are there of length up to L over an alphabet of size a?

Run:  pytest -k differential
"""


def find_counterexample(candidate, oracle, alphabet, max_len):
    raise NotImplementedError
