"""
A bitset: a set of small ints stored as the bits of one Python int
Topic: 02.11  |  Priority: P1  |  Chapter: concepts/bit-manipulation.html (exercise 8)

Bitset(size) holds a set of ints from range(size). Member i is bit i of ONE
Python int, kept in self.bits (the tests read it). The empty set is bits == 0;
{0, 3} is bits == 0b1001 == 9. Nothing else may grow with the number of
members: no Python set, no list of booleans, no bytearray of 0s and 1s kept
alongside. The tests measure the memory a dense Bitset holds.

Bitset(size, items=())   size >= 0; add every item (each in range(size)).
b.add(i)                 i must be in range(size), else IndexError.
b.discard(i)             remove i if present; absent (or out of range) is fine.
                         Careful: XOR toggles, so it ADDS an absent i.
i in b                   True or False. Out-of-range ints are just False.
len(b)                   number of members.
iter(b)                  members in increasing order.
b | c, b & c, b - c      union, intersection, difference, as NEW Bitsets of
                         the same size. Sizes must match, else ValueError.
                         Don't change b or c.
b == c                   same size and same members.

The work rule: no operation may walk every bit position from 0 to size.
The tests build bitsets of a million positions with a handful of members
and call len, |, &, - and iter a thousand times each. A loop over a million
positions per call takes about 100 ms in Python, so a thousand calls blow
the 10 s limit; one int operation on a million-bit number takes microseconds.
iter must take one step per MEMBER (section 6: x & -x and bit_length()).

Python ints are immutable, so every bits |= ... builds a new int: an add on
a million-bit set copies ~125 KB. That's fine here (it's done in C), and it's
the price of using one int. Section 9 of the chapter says when you'd pick a
list of 64-bit words instead.

Before you code (say it out loud)
---------------------------------
Which one operator is each of union, intersection and difference? How many
machine words does a million-bit union touch? Why must discard not use ^?
What does iter cost for a set with m members out of a million positions?

Run:  python3 -m pytest -k bitset
"""


class Bitset:
    def __init__(self, size: int, items=()):
        raise NotImplementedError

    def add(self, i: int) -> None:
        raise NotImplementedError

    def discard(self, i: int) -> None:
        raise NotImplementedError

    def __contains__(self, i) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __or__(self, other: "Bitset") -> "Bitset":
        raise NotImplementedError

    def __and__(self, other: "Bitset") -> "Bitset":
        raise NotImplementedError

    def __sub__(self, other: "Bitset") -> "Bitset":
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        raise NotImplementedError
