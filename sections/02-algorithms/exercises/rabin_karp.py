"""
Rabin-Karp: compare numbers, not strings
Topic: 02.12  |  Priority: P1  |  Chapter: concepts/string-algorithms.html (exercise 4)

A window of text can be turned into one number (its hash). Sliding the
window one step changes that number in O(1): take the old first character
out, shift, put the new last character in. That's a rolling hash. These
three pieces build on each other.

The tests MEASURE the work. `text` and `pattern` are read-only sequences
that count every character you read (s[i], for-loops, comparing or hashing
a slice). Use len(s), s[i], s[i:j] and for-loops on them; they have no
string methods. Slices are cheap views, but reading their characters is
counted. Don't use re, str.find, str.index, "".join and friends: the point
is to build it. Each test also runs under a 3-second cap. Turning the text
into a list of ord() values first is fine (and reads it once), but then the
read count can't see what you do with the list: recomputing every window
from it is n * m steps, about 20 seconds here, while O(n + m) is a small
fraction of a second.

The hash, exactly (the tests check the numbers):

    H(s) = (ord(s[0]) * B**(m-1) + ord(s[1]) * B**(m-2) + ... + ord(s[m-1])) % M

with m = len(s), base B and modulus M. Use MOD = 2**61 - 1 (a prime) unless
you are told otherwise.

1. window_hashes(text, m, base, mod=MOD) -> list[int]
   H of every length-m window: [H(text[0:m]), H(text[1:m+1]), ...], that is
   len(text) - m + 1 numbers (an empty list if m > len(text)). m >= 1.
   window_hashes("abcd", 2, 100, 10**9) -> [9798, 9899, 10000]
   (ord("a") = 97, so H("ab") = 97 * 100 + 98 = 9798).
   Target: O(n). The test allows about 3 reads per character of text;
   recomputing each window from scratch needs n * m (m up to 5,000).

2. find_all(text, pattern, base=None, mod=MOD) -> list[int]
   Every start index where pattern occurs in text, in increasing order,
   overlaps included. pattern has at least one character.
   find_all("abababa", "aba") -> [0, 2, 4].
   If base is None, pick a random base in [256, mod - 1] (why random? the
   chapter's section 5 says). A matching hash can be a COLLISION: two
   different strings with the same number. The test passes tiny moduli
   like 7, where collisions are everywhere, and still expects the exact
   answer. So check every hash match before you report it.
   Target: O(n + m) expected, plus m for each real match you check.
   Text "aaa...a", pattern "aa...ab" makes the naive scan cost n * m.

3. SubstringHasher(text, base=None, mod=MOD)
   Read text once in __init__ (the test allows about 2 reads per
   character), then answer
       equal(i, j, length) -> bool
   "is text[i : i+length] == text[j : j+length]?" in O(1), WITHOUT reading
   text again (the test checks that equal() reads zero characters). Indexes
   are valid and length >= 0. Trusting a 61-bit hash with a random base is
   fine here: two different strings collide with probability about
   length / 2**61.
   Hint: prefix hashes. If P[k] = H(text[:k]), what is H(text[i:j]) in
   terms of P[i], P[j] and a power of B? Store the powers too.

Before you code (say it out loud)
---------------------------------
1. Brute force and its cost on text "a" * n, pattern "a" * (m-1) + "b"?
2. Write the slide step for base 10 on paper: 314 -> 141. Which digit's
   value do you subtract, and what do you multiply by?
3. Why keep the numbers mod M? (What would Python's big ints cost you on a
   1,000-character window?) What breaks if you trust a hash match without
   checking it?

Run:  python3 -m pytest -k rabin_karp
"""

MOD = (1 << 61) - 1


def window_hashes(text, m: int, base: int, mod: int = MOD) -> list:
    raise NotImplementedError


def find_all(text, pattern, base=None, mod: int = MOD) -> list:
    raise NotImplementedError


class SubstringHasher:
    def __init__(self, text, base=None, mod: int = MOD):
        raise NotImplementedError

    def equal(self, i: int, j: int, length: int) -> bool:
        raise NotImplementedError
