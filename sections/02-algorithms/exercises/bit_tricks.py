"""
Bit tricks: one step per set bit, pairs that cancel, and a 32-bit adder
Topic: 02.11  |  Priority: P1  |  Chapter: concepts/bit-manipulation.html (exercises 4-6)

For 4a-4c the tests pass in a special int that counts every operation done
on it (& | ^ ~ + - << >> and comparisons). `while x:` and x.bit_length() are
free. A loop over every bit position gives right answers but fails the
budget. Don't use bin, hex, oct, format, str, repr, f-strings or
x.bit_count() anywhere in this file: the point is to build these yourself.
Numbers below match the exercise numbers in the chapter.

4a. popcount(x) -> int
    How many 1 bits x has. x >= 0, and may be far wider than 64 bits.
    popcount(0) -> 0, popcount(13) -> 3 (13 is 1101), popcount(2**100) -> 1.
    Budget: 6 operations per 1 bit, plus 4, however wide x is. Looking at
    every position is too slow: 2**1000 + 1 has 2 ones and 1,001 positions.
    Section 6's trick visits only the ones. One more test hands popcount and
    bit_positions a plain int with a million positions and three 1s, and
    allows 1 second.

4b. bit_positions(x) -> list[int]
    The positions of x's 1 bits, smallest first. x >= 0.
    bit_positions(0) -> [], bit_positions(13) -> [0, 2, 3], bit_positions(2**70) -> [70].
    Budget: 8 operations per 1 bit, plus 4, however wide x is. x.bit_length()
    is allowed (it's free here); it tells you where the highest 1 is.

4c. next_power_of_two(x) -> int
    The smallest power of two that is >= x. x >= 1.
    1 -> 1, 5 -> 8, 8 -> 8, 9 -> 16, 2**100 + 1 -> 2**101.
    Hash tables round their capacity up like this. Budget: 6 operations for
    ANY x, comparisons included, so doubling a guess until it's big enough
    (one comparison per doubling) is too slow for 2**1000.

5.  single_number(nums) -> int
    Every value in nums appears exactly twice, except one value that appears
    once. Return that one. Values are any ints, negatives included.
    [4, 1, 2, 1, 2] -> 4.   [-7] -> -7.
    O(n) time and O(1) extra memory: the test measures peak memory with
    tracemalloc on 200,001 numbers, and a set, a dict, a Counter or a sorted
    copy all go far over. Don't change the input list (sorting it in place
    also allocates a big buffer).

6.  add32(a, b) -> int
    a and b are signed 32-bit ints (-2**31 <= a, b < 2**31). Return a + b the
    way a 32-bit CPU would: wrapping around on overflow, like an odometer.
    add32(2, 3) -> 5.   add32(-1, 1) -> 0.   add32(2**31 - 1, 1) -> -2**31.
    The catch: add32, and any helper it calls, may not use + or - between
    two numbers (no a + b, a - b, a += b, sum()). + or - with a constant is
    fine: i += 1, or section 9's u - (1 << 32). A constant is a number literal
    or an ALL_CAPS name like MASK = 0xFFFFFFFF. Unary minus (-x) is fine too.
    Build the adding from &, ^ and <<: XOR adds without carrying, AND then
    << 1 is the carry. Python ints never overflow, so on negative numbers
    the carry grows forever unless you cut every step to 32 bits (section 9).
    The tests stop any test that runs past 5 seconds.

Before you code (say it out loud)
---------------------------------
For 4a: what does x - 1 look like next to x, bit by bit? How many times does
your loop run for 2**1000? For 4b: which expression keeps only the lowest 1?
For 4c: which x have the answer 16, and what do they share in binary? Careful
with an x that is already a power of two. For 5: which two facts about XOR
make every pair vanish, and why doesn't the order of the list matter? For 6: draw 0110 + 0011
as "add without carry" plus "the carries, shifted left". When do you stop?

Run:  python3 -m pytest -k bit_tricks
"""


def popcount(x: int) -> int:
    raise NotImplementedError


def bit_positions(x: int) -> list:
    raise NotImplementedError


def next_power_of_two(x: int) -> int:
    raise NotImplementedError


def single_number(nums: list) -> int:
    raise NotImplementedError


def add32(a: int, b: int) -> int:
    raise NotImplementedError
