"""
Reservoir sampling: a fair random sample from a stream of unknown length
Topic: 02.13  |  Priority: P2

Problem
-------
Sections 3 to 5 of the chapter. Lines arrive one at a time and you don't
know how many there will be. Keep a fair random sample of k of them, in one
pass, holding only k items.

    rng = random.Random(7)
    reservoir_sample(iter(range(1_000_000)), 3, rng)   -> e.g. [412907, 88, 730511]
    reservoir_sample(iter("ab"), 5, rng)               -> ['a', 'b'] (in some order)

1. reservoir_sample(stream, k, rng) -> list
   - stream is any iterable, usually an iterator you can read only once.
   - Return k items chosen uniformly at random without replacement: every
     set of k items must be equally likely. The order of the returned list
     doesn't matter.
   - Fewer than k items in the stream: return all of them. k == 0: [].
   - Use only rng (a random.Random) for randomness, never the random
     module's global functions, so a seed makes runs repeatable.
   - Target: O(n) time, O(k) memory.

2. weighted_reservoir_sample(stream, k, rng) -> list
   - stream yields (item, weight) pairs with weight > 0 (floats allowed).
   - Return k items (just the items, not the pairs) sampled without
     replacement in proportion to weight: the result must have the same
     distribution as "pick one item with probability weight / total weight,
     remove it, repeat k times". With k == 1, an item of weight 3 next to
     one of weight 1 is picked 3/4 of the time.
   - Fewer than k pairs: return all the items. k == 0: [].
   - Target: O(n log k) time, O(k) memory.

What the tests measure
----------------------
- Fairness: thousands of seeded runs on small streams. Every k-subset (or
  every item, for the weighted version) must show up about as often as its
  exact probability says. The bound is a chi-square statistic set so loose
  that a correct solution passes on any seed, while an off-by-one in the
  keep probability (keeping line i, counted from 1, with k / (i - 1)
  instead of k / i) or always replacing the same slot is far over it.
- Memory: a generator of 200,000 fresh integers goes in, under tracemalloc.
  Peak extra memory must stay under 64 KB. list(stream) costs megabytes.
- One pass: the stream is an iterator, so it can't be read twice.

Before you code (say it out loud)
---------------------------------
1. With k = 1: why does keeping item i with probability 1/i leave item 1
   with a 1/n chance at the end? Multiply the survival chances for n = 4.
2. With k slots: an item already in the reservoir. What's the chance the
   next item kicks it out? Why does that make the induction work?
3. Weighted: why give each item a random tag and keep the k best tags?
   Why is the tag u ** (1 / w) and not u * w? (Try weights 1 and 3, k = 1.)
4. What changes if the sample must be merged from 10 machines?

Run:  pytest -k reservoir_sample
"""


def reservoir_sample(stream, k, rng):
    raise NotImplementedError


def weighted_reservoir_sample(stream, k, rng):
    raise NotImplementedError
