"""
Jump consistent hash
Topic: 02.15  |  Priority: P2

Problem
-------
The "Go deeper" box in section 10 of the chapter. Map a 64-bit integer key
to one of num_buckets buckets numbered 0 .. num_buckets-1, with no ring and
no memory at all, so that going from n to n+1 buckets moves only 1/(n+1)
of the keys, all of them into the new bucket n.

    jump_hash(1, 10) -> 6
    jump_hash(0, 1)  -> 0          (one bucket: everything is bucket 0)

Requirements
------------
- jump_hash(key, num_buckets) -> int in range(num_buckets).
  0 <= key < 2**64. ValueError if num_buckets < 1.
- Use exactly the algorithm from Lamping and Veach (Google, 2014), so the
  numbers match every other implementation. The key drives a 64-bit linear
  congruential generator:
      key = (key * 2862933555777941757 + 1) mod 2**64
  and from the current bucket b you jump forward to
      j = floor((b + 1) * 2**31 / ((key >> 33) + 1))
  computed in floating point as the paper does: (b + 1) times
  (float(2**31) / float((key >> 33) + 1)), then int(). Start at b = -1,
  j = 0. While j < num_buckets: set b = j and take the next jump. Return b.
  Python ints never overflow, so the "mod 2**64" is your job.
- O(log n) expected jumps: each jump multiplies the bucket number by
  about 1 / (a random number in (0, 1]).

What the tests measure
----------------------
- Exact values for 14 (key, num_buckets) pairs, computed offline from the
  paper's C++ code.
- Going from n to n + 1 buckets, every key either stays or moves to bucket
  n, and about 1/(n + 1) of them move.
- 10,000 keys over 10 buckets land within 10% of 1,000 each.
- 2,000 keys with num_buckets = 2**31 - 1 under a 10 s cap. The O(n)
  version that checks every bucket count from 1 to n would need about
  2 billion steps per key.

Before you code (say it out loud)
---------------------------------
1. Think of the key's bucket as it would be for 1, 2, 3, ... buckets. When
   the count goes from n to n + 1, with what probability must the key jump
   to the new bucket? Why does that give an even spread?
2. Why can the algorithm skip straight to the next bucket count where the
   key jumps, instead of checking each one?
3. What can't it do that a ring can? (Hint: remove bucket 3 of 10.)

Run:  pytest -k jump_hash
"""


def jump_hash(key: int, num_buckets: int) -> int:
    raise NotImplementedError
