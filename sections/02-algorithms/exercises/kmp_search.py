"""
KMP: never read a character of the text twice
Topic: 02.12  |  Priority: P1  |  Chapter: concepts/string-algorithms.html (exercise 5)

When a match breaks after k characters, you already know what those k
characters were: they're the first k characters of the pattern. The
failure table stores, for every k, how much of that matched part is still
useful as the start of a new match. With it, the search only ever moves
forward through the text.

The tests MEASURE the work. `text` and `pattern` are read-only sequences
that count every character you read. Use len(s), s[i] and for-loops; they
have no string methods and (for kmp_find_all's text) no slicing. Don't use
re, str.find, "".join and friends, or the `in` operator (you won't need it;
`for c in s` loops are fine).

1. failure_table(pattern) -> list[int]
   fail[i] = length of the longest PROPER prefix of pattern[: i + 1] that
   is also a suffix of it ("proper" = not the whole thing, so fail[0] = 0).
   failure_table("ababaca") -> [0, 0, 1, 2, 3, 0, 1]
   failure_table("aaaa")    -> [0, 1, 2, 3]
   Target: O(m). The test allows about 8 reads per character; trying every
   prefix length for every i needs m**2 or more.

2. kmp_find_all(text, pattern) -> list[int]
   Every start index where pattern occurs in text, in increasing order,
   overlaps included. pattern has at least one character.
   kmp_find_all("abababa", "aba") -> [0, 2, 4]
   Target: O(n + m) in the WORST case, and the text is read FORWARD ONLY:
   the test's text raises an error if you ever read text[i] after reading
   some text[j] with j > i (looping over it a second time counts as going
   back). Reading the same text[i] again is allowed, but
   the cheapest code reads it once into a variable. The test allows about
   3 reads per text character, and about 8 per pattern character plus 6
   per text character for the pattern (table included).

3. count_in_stream(chunks, pattern) -> int
   The text arrives as an iterable of str chunks (think network packets),
   too big to keep. Count how many times pattern occurs in the
   concatenation of all chunks, overlaps included. Matches can straddle
   chunk boundaries. pattern is a plain str with at least one character.
   count_in_stream(["ab", "aba", "", "ba"], "aba") -> 3
   (the stream is "abababa", and "aba" starts at 0, 2 and 4)
   Target: O(n + m) time, O(m) extra memory. The test streams megabytes
   and measures your peak memory, so keeping the whole text (or every
   chunk) fails, and so does a buffer of the last m characters that you
   re-check at every position (n * m time: the test uses m = 300,000).

Before you code (say it out loud)
---------------------------------
1. You matched "ababa" of the pattern "ababaca", then the next text
   character is "b", not "c". Without looking at the text again, what do
   you know the last five text characters are? Which shorter start of the
   pattern do they end with?
2. Why does the while loop that falls back through the table never make the
   whole search worse than about 2n steps? (What goes up by at most 1 per
   text character, and can never go below 0?)
3. How is building the table the same algorithm as searching?

Run:  python3 -m pytest -k kmp_search
"""


def failure_table(pattern) -> list:
    raise NotImplementedError


def kmp_find_all(text, pattern) -> list:
    raise NotImplementedError


def count_in_stream(chunks, pattern: str) -> int:
    raise NotImplementedError
