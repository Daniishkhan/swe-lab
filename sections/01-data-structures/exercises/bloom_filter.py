"""
Bloom filter
Topic: 01.12  |  Priority: P1

Problem
-------
Build sections 2 to 5 of the chapter: a set that answers "have I seen this?"
in about 10 bits per item, at the price of a small, known chance of a wrong
"yes". A "no" is always right.

    bf = BloomFilter(capacity=1000, error_rate=0.01)
    bf.num_bits    -> 9586     (about 9.6 bits per item)
    bf.num_hashes  -> 7
    bf.add("apple")
    "apple" in bf  -> True     (always: no false negatives)
    "banana" in bf -> False    (or, rarely, True: a false positive)

Requirements
------------
- BloomFilter(capacity, error_rate): sized for `capacity` items at a false
  positive rate of `error_rate`. Raise ValueError unless capacity >= 1 and
  0 < error_rate < 1. Use the sizes from section 4, exactly:
      num_bits   = ceil(-capacity * ln(error_rate) / (ln 2) ** 2)
      num_hashes = max(1, round(num_bits / capacity * ln 2))
- add(item) and `item in bf` (__contains__): items are str. Each touches
  num_hashes bits, so both are O(k) whatever the number of items.
- Store the bits packed, 8 per byte (a bytearray of ceil(num_bits / 8)
  bytes). Never store the items themselves.
- to_bytes(): the bit array as bytes, ceil(num_bits / 8) long. Bit i lives
  in byte i // 8 (which bit inside the byte is up to you).
- union(other): a NEW filter holding the bitwise OR of both bit arrays. It
  answers "maybe" for anything added to either one. Raise ValueError if the
  two filters differ in num_bits or num_hashes. Don't modify either input.
- Hash with hashlib (for example blake2b or sha256 of item.encode("utf-8")),
  never the built-in hash(): Python salts string hashes per process, so a
  filter saved by one process would be garbage in the next. You don't need
  k separate hash functions: section 8's double hashing turns one digest
  into all k positions.

What the tests measure
----------------------
- No false negatives, ever (20,000 items).
- The false positive rate at capacity, on 50,000 to 100,000 strings that
  were never added, must stay under 1.5x the target (1% and 0.1%). A filter
  with one hash function and the same bits is near 10%.
- Memory: adding 100,000 items to a filter sized for them (about 117 KB of
  bits) must peak under 400 KB of new allocations. A set of the items, or
  a list of 958,506 Python bools, uses several MB.
- add and lookup touch only k bits: 200 adds and 400 lookups on a filter
  with 1.2 MB of bits must allocate under 100 KB. A Python int used as the
  bit array (bits |= 1 << i), or a copy of the bytearray per add, builds a
  new 1.2 MB object every time.
- to_bytes() is byte-for-byte identical in two Python processes started
  with different PYTHONHASHSEED values (so built-in hash() fails).
- union() equals a filter built from both inputs' items directly.

Before you code (say it out loud)
---------------------------------
1. Why can a Bloom filter say "maybe" for an item never added, but never
   "no" for an item that was?
2. Why does adding hash functions first lower, then raise, the false
   positive rate for a fixed number of bits?
3. Why can't you delete an item by clearing its bits?
4. Why is the union of two filters an OR, and why must the shapes match?

Run:  pytest -k bloom_filter
"""


class BloomFilter:
    def __init__(self, capacity: int, error_rate: float):
        raise NotImplementedError

    @property
    def num_bits(self) -> int:
        raise NotImplementedError

    @property
    def num_hashes(self) -> int:
        raise NotImplementedError

    def add(self, item: str) -> None:
        raise NotImplementedError

    def __contains__(self, item: str) -> bool:
        raise NotImplementedError

    def union(self, other: "BloomFilter") -> "BloomFilter":
        raise NotImplementedError

    def to_bytes(self) -> bytes:
        raise NotImplementedError
