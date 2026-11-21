"""
HyperLogLog
Topic: 01.12  |  Priority: P1

Problem
-------
Build section 7 of the chapter: count the DISTINCT items in a stream using a
fixed, tiny amount of memory. With p = 14 there are m = 2**14 = 16,384
registers, and the count is typically within about 0.8% of the truth
(standard error 1.04 / sqrt(m)), whether there are a thousand distinct items
or a billion.

    h = HyperLogLog(p=14)
    for w in "the cat saw the other cat".split():
        h.add(w)
    h.count()  -> 4      (the, cat, saw, other)
    h.m        -> 16384

Requirements
------------
- HyperLogLog(p=14): m = 2**p registers, all 0. Raise ValueError unless
  4 <= p <= 16. Expose m.
- add(item): item is a str. Hash it to 64 bits with hashlib, for example
      x = int.from_bytes(hashlib.blake2b(item.encode(), digest_size=8).digest(), "big")
  (never the built-in hash(): it changes from process to process). Then:
      j    = the top p bits of x                         (which register)
      rest = the other 64 - p bits
      rho  = (number of leading zeros of rest, as a (64 - p)-bit number) + 1
      register[j] = max(register[j], rho)
  O(1) per add.
- count(): the estimate, rounded to an int.
      raw = alpha * m * m / sum(2 ** -register[j] for every j)
      alpha = 0.673 if m == 16, 0.697 if m == 32, 0.709 if m == 64,
              otherwise 0.7213 / (1 + 1.079 / m)
  Small counts: if raw <= 2.5 * m and V registers are still 0 (V > 0),
  return round(m * ln(m / V)) instead ("linear counting", section 7).
  Otherwise return round(raw). An empty sketch counts 0.
- merge(other): a NEW sketch whose registers are the element-wise max of
  both. It counts the union. Raise ValueError if p differs. Don't modify
  either input.
- Memory: the m registers and nothing that grows with the number of items.
  A bytearray(m) is the natural fit (a register never exceeds 64 - p + 1).

What the tests measure
----------------------
- Within 1 on tiny inputs, within max(2, 2.5%) for 1 to 1,000 distinct items,
  and within 4 standard errors (4 x 1.04 / sqrt(m)) for 20,000 to 200,000
  distinct items at p = 10, 12 and 14. Using one register (2 ** max rho)
  is off by a factor of two or more; skipping linear counting is off by
  thousands on small inputs.
- Adding duplicates never changes the count.
- Memory: adding 200,000 distinct items must peak under 300 KB of new
  allocations (a set of the items takes over 8 MB).
- merge() gives exactly the count of one sketch fed both streams.
- Counts are identical in two processes with different PYTHONHASHSEED.

Before you code (say it out loud)
---------------------------------
1. Why does seeing a hash that starts with 10 zeros suggest about 2**11
   distinct items? Why does adding the same item again change nothing?
2. Why split into m registers instead of keeping one maximum?
3. Why the harmonic mean, and not the plain average of 2 ** register?
4. Why is merging two sketches an element-wise max, and why does that give
   the union and not the sum?

Run:  pytest -k hyperloglog
"""


class HyperLogLog:
    def __init__(self, p: int = 14):
        raise NotImplementedError

    @property
    def m(self) -> int:
        raise NotImplementedError

    def add(self, item: str) -> None:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def merge(self, other: "HyperLogLog") -> "HyperLogLog":
        raise NotImplementedError
