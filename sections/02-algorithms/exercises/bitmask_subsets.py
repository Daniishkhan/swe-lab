"""
Bitmask subsets: every subset, every sub-subset, every k-subset
Topic: 02.11  |  Priority: P1  |  Chapter: concepts/bit-manipulation.html (exercise 7)

A mask is an int whose bit i says "item i is in". Counting from 0 to 2**n - 1
visits every subset of n items exactly once. These three functions use that
picture. Don't use itertools here; the point is to drive the bits yourself.
The tests use masks as wide as 60 bits, where looping over every number up
to the mask (2**60 of them) never finishes: work must grow with the number
of answers, not with the size of the mask. A test that runs past 5 seconds
is stopped.

7a. subsets(items) -> list[list]
    Every subset of items, in MASK ORDER: result[mask] holds items[i] for
    each bit i set in mask, in the order they appear in items.
    subsets(["a", "b", "c"]) ->
      [[], ["a"], ["b"], ["a", "b"], ["c"], ["a", "c"], ["b", "c"], ["a", "b", "c"]]
    subsets([]) -> [[]]. Don't change the input list.
    O(n * 2**n): there are 2**n subsets, each up to n long.

7b. submasks(mask) -> list[int]
    Every s with s & ~mask == 0 (every subset of the bits of mask), from
    largest to smallest, ending with 0. mask >= 0.
    submasks(0b1010) -> [0b1010, 0b1000, 0b0010, 0b0000] == [10, 8, 2, 0]
    submasks(0) -> [0].
    O(2**k) where k is the number of 1 bits in mask, NOT O(mask). The test
    asks for the submasks of a mask with 3 bits spread over 51 positions:
    8 answers. Section 8's "subtract one, then AND with the mask" step does it.

7c. masks_with_k_bits(n, k) -> list[int]
    Every mask below 2**n with exactly k bits set, smallest first.
    0 <= k <= n. masks_with_k_bits(4, 2) -> [3, 5, 6, 9, 10, 12].
    masks_with_k_bits(5, 0) -> [0]. masks_with_k_bits(3, 3) -> [7].
    O(C(n, k)) masks, a little work each. The test asks for n = 60, k = 2
    (1,770 masks), where checking all 2**60 numbers never finishes. Build them
    directly: recursion that chooses positions works; so does Gosper's hack
    (section 8's Go deeper box) that jumps from one mask to the next.

Before you code (say it out loud)
---------------------------------
For 7a: write the 8 masks for 3 items in binary, next to the subsets they
stand for. For 7b: trace s = (s - 1) & mask by hand for mask = 1010: why does
it skip every number that isn't a submask? For 7c: how many answers are
there for n = 60, k = 2, and how many numbers below 2**60?

Run:  python3 -m pytest -k bitmask_subsets
"""


def subsets(items: list) -> list:
    raise NotImplementedError


def submasks(mask: int) -> list:
    raise NotImplementedError


def masks_with_k_bits(n: int, k: int) -> list:
    raise NotImplementedError
