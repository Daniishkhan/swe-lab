"""
Huffman coding: the shortest prefix-free code
Topic: 02.10  |  Priority: P1

Problem
-------
Section 7 of the chapter. You get a dict from symbol to how often it
appears. Give every symbol a code word made of "0" and "1" characters so
that:

- the code is PREFIX-FREE: no code word is the start of another one, so a
  stream of bits can be read back without separators, and
- the total length of the encoded text, sum(freq[s] * len(code[s])), is as
  small as possible.

huffman_code(freqs) returns that dict from symbol to code word.

    huffman_code({"a": 45, "b": 13, "c": 12, "d": 16, "e": 9, "f": 5})
        -> for example {"a": "0", "c": "100", "b": "101", "d": "111",
                        "f": "1100", "e": "1101"}
           total 45*1 + 12*3 + 13*3 + 16*3 + 5*4 + 9*4 = 224 bits
    huffman_code({"x": 7})   -> {"x": "0"}     # one symbol still needs one bit
    huffman_code({})         -> {}

Many different codes reach the same smallest total (swap 0 and 1 anywhere,
or break ties between equal counts the other way). The tests accept any of
them: they check prefix-freeness and the total, not the exact bits.

Requirements
------------
- Counts are positive integers. Symbols are any hashable values.
- Don't modify the caller's dict.
- O(n log n) for n symbols. Building the code words from the tree costs
  the total length of all code words, which is fine.

What the tests measure
----------------------
Every count is wrapped in a number that counts comparisons; adding two of
them gives another counted number.
- 2,000 symbols: under 12 n log2 n comparisons (about 263,000). Finding
  the two smallest by scanning every remaining tree, every round, needs
  about 4 million.
- 524,288 equal plain-int counts in under 10 seconds (a heap takes 1 to 3).
  A sorted list with list.pop(0) or bisect.insort uses few comparisons,
  but each of those calls shifts every item after it, so the whole build
  is O(n^2) and takes over 40 seconds.
- Optimality: against brute force (every way to pair up trees) on small
  inputs, against a total known by construction (2^k equal counts need
  exactly k bits each), and against totals computed offline.

Before you code (say it out loud)
---------------------------------
1. Draw a prefix-free code as a binary tree. Where do the symbols sit, and
   what is a code word's length in the picture?
2. Why must the two rarest symbols be able to sit together, as siblings,
   at the deepest level of some best tree? (Exchange argument.)
3. After you merge the two rarest into one "super symbol" with the sum of
   their counts, why is the rest the same problem, one symbol smaller?
4. Ties: two trees with equal counts. Will a heap of (count, tree) tuples
   ever try to compare two trees? How do you stop that?

Run:  pytest -k huffman_code
"""


def huffman_code(freqs: dict) -> dict:
    raise NotImplementedError
