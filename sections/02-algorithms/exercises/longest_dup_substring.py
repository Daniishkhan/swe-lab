"""
Longest repeated substring: binary search + rolling hash
Topic: 02.12  |  Priority: P1  |  Chapter: concepts/string-algorithms.html (exercise 6)

Problem
-------
longest_dup_substring(s) -> str
Return a longest substring that occurs in s at least twice (the two
occurrences may overlap). If several have the longest length, return any
one of them. If no character repeats, return "".

    "banana"      -> "ana"   (at 1 and 3, overlapping)
    "abcd"        -> ""
    "aaaaa"       -> "aaaa"
    "abcXabcYabc" -> "abc"

Return the answer as a slice of the input, s[i:j] (the test reads it
back), or as a str.

How the test measures work
--------------------------
s is a read-only sequence that counts every character you read: s[i],
for-loops, and hashing or comparing a slice s[i:j] (which reads its j - i
characters). It has no string methods. Don't use re, str.find, "".join
and friends.

The test allows about 60 reads per character for n = 20,000, and caps each
test at 5 seconds (a list of ord() values is fine, but the clock still sees
what you do with it). That rules out:
  - every pair of starts, comparing forward: n^2 / 2 and up;
  - a set of slices per length (hashing a slice reads all of it): n * L per
    length you try;
  - trying lengths 1, 2, 3, ... in order with a rolling hash: 2n per length,
    and on "aaa...a" the answer is 19,999 long.
Target: O(n log n) expected. Two ideas, each from the chapter:
  1. If some length-L substring repeats, so does some length-(L-1) one (drop
     its last character). So "is there a repeat of length L?" is a yes...yes,
     no...no question: binary search on L (chapter 02.03).
  2. "Is there a repeat of length L?" in O(n): put the rolling hash of every
     length-L window in a dict. Use mod 2**61 - 1 and a random base. Decide
     whether you check a hash match character by character (and say what
     that costs), or trust it (and say how likely a false repeat is).

Before you code (say it out loud)
---------------------------------
1. Brute force and its cost?
2. Why is binary search on the length allowed here? What would break it?
3. How many lengths does the binary search try for n = 20,000? How much
   does each try cost?

Run:  python3 -m pytest -k longest_dup_substring
"""


def longest_dup_substring(s) -> str:
    raise NotImplementedError
