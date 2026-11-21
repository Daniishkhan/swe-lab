"""
Bisect with versions you can't test
Topic: 13.06  |  Priority: P0

Problem
-------
Section 7 of the chapter. Versions 1..n of a program, oldest first. At some
version a bug went in, and every version from then on has it. Version n,
the latest, is known to be bad. Find the first bad version with as few test
runs as possible, the way `git bisect` does.

The twist: some versions can't be tested at all (they don't build, or the
test needs a file that didn't exist yet). For those, is_bad returns None,
and you have to test a neighbor instead. This is `git bisect skip`.

    # versions 1..8, the first bad one is 6, and version 5 doesn't build
    first_bad(8, is_bad)   -> (5, 6)    # "5 or 6": 5 can't be tested
    # the same, but every version builds
    first_bad(8, is_bad)   -> (6, 6)

first_bad(n, is_bad) -> tuple[int, int]
  - is_bad(v), for 1 <= v <= n, returns True (bad), False (good) or None
    (can't be tested). Every testable version before the first bad one is
    good; every testable version from it on is bad. Version n is bad and
    testable, so you never need to ask about it.
  - Return (lo, hi), the narrowest range the answers can prove:
      hi = the first testable version that is bad,
      lo = one more than the last testable version before it that is good
           (or 1 if there is none).
    Every version from lo to hi - 1 can't be tested, so the first bad
    version could be any of lo..hi. With nothing untestable in the way,
    lo == hi and you've found it exactly.
  - Ask about each version at most once. Every call is a build and a test
    run, so remember the answers.

What the tests measure
----------------------
- Calls to is_bad, counted.
  * With no untestable versions: at most ceil(log2 n) + 1 calls, which is
    21 for n = 1,000,000: binary search needs ceil(log2 n), plus one spare.
    That's the loop from the binary search chapter (section 3 there).
  * With untestable versions: the same, plus 2 for every call that answers
    None. You couldn't have known it was untestable, and stepping around it
    can cost one more test.
  Testing versions one by one costs up to n calls and fails.
- Every n up to 10, with every set of untestable versions and every first
  bad version, against the answer built from the definition above.
- Blocks of untestable versions right before the first bad one, starting at
  it, and in the middle of the range; every 2nd version untestable; every
  4,096th version untestable (where the first probes of a binary search
  land).

Before you code (say it out loud)
---------------------------------
1. Keep two facts true: `good` is the last version known good (0 at the
   start: pretend version 0 is good), `bad` the first version known bad
   (n at the start). Where is the first bad version?
2. The version in the middle is untestable. Which one do you test instead,
   and why one close to the middle?
3. When do you stop? What is left between good and bad at that point?
4. Why can't you treat an untestable version as good, or as bad?

Run:  pytest -k bisect_skip
"""


def first_bad(n, is_bad):
    raise NotImplementedError
