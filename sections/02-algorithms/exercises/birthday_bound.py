"""
Birthday bound: how long must a random ID be?
Topic: 02.16  |  Priority: P1

Problem
-------
Section 11 of the chapter. You give every new object a random ID drawn
uniformly from m possible values (m = 2**b for b random bits). With n
objects, how likely is it that two share an ID, and how many bits do you
need to keep that chance below a target?

    expected_colliding_pairs(23, 365)      -> 0.6931...   # 253 pairs / 365
    collision_probability(23, 365)         -> 0.507297... # the birthday paradox
    collision_probability(1000, 2**64)     -> 2.70779e-14
    collision_probability(10**9, 2**64)    -> 0.026741    # a billion 64-bit IDs
    bits_needed(10**9, 1e-6)               -> 79

Requirements
------------
- expected_colliding_pairs(n, m) -> float: the average number of pairs
  (i < j) whose IDs are equal. One line, by linearity of expectation.
- collision_probability(n, m) -> float: the chance that at least two of n
  independent uniform draws from m values are equal.
  * n <= 1 gives 0.0; n > m gives 1.0 (more objects than IDs).
  * Accurate to a relative error of 1e-6, for every n and m the tests use:
    m from 1 to 2**64, n up to 10**12.
  * Fast: n = 10**9 must answer in well under a second, so the exact
    product of n terms is out for big n. The tests cap each test at 2 s.
- bits_needed(n, max_probability) -> int: the smallest b >= 0 with
  collision_probability(n, 2**b) <= max_probability. Raise ValueError
  unless 0 < max_probability < 1.

Where the precision goes (read before you code)
-----------------------------------------------
- The exact answer is 1 - (1 - 0/m)(1 - 1/m)...(1 - (n-1)/m). Multiplying
  those floats directly fails for m = 2**64: 1 - 1/2**64 rounds to exactly
  1.0, so the product says "no collision ever".
- The chapter's 1 - e^(-n(n-1)/2m) is very good when n is big, but about
  1.4% off for n = 23, m = 365. Its relative error is at most about
  0.4 / n, so it is good enough for 1e-6 only once n is near a million.
  (Its first ignored term is n^3 / 6m^2 inside the exponent.)
- 1 - e^(-x) for tiny x loses most of its digits. The math module has
  functions made for "log of 1 + tiny" and "e^tiny - 1". Find them.

What the tests check
--------------------
Values worked out offline to 15+ digits (birthday paradox, 50% points for
32-bit IDs, a case where the closed form is
2e-6 off at n = 150,000, tiny probabilities for 64-bit IDs, a billion IDs), an exact
brute force for every m <= 40, monotonic growth in n, n = 10**9 and
n = 10**12 under the 2 s cap, and bits_needed at known answers (two of
them where inverting the closed form picks one bit too few).

Before you code (say it out loud)
---------------------------------
1. Why is the chance of a collision about n^2 / 2m, and not n / m?
2. Around how many objects does a 32-bit random ID start colliding? A
   64-bit one? Why "square root"?
3. A short-URL service uses 7 random base-62 characters for 100 million
   links. Is checking for collisions on insert optional?

Run:  python3 -m pytest -k birthday_bound
"""


def expected_colliding_pairs(n, m):
    raise NotImplementedError


def collision_probability(n, m):
    raise NotImplementedError


def bits_needed(n, max_probability):
    raise NotImplementedError
