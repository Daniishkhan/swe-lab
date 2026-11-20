"""
Trie patterns: top suggestions, longest prefix match, maximum XOR
Topic: 01.06  |  Priority: P1

Problem
-------
Sections 7, 10 and 11 of the chapter. Write your own tries here (dicts or
small node classes); no third-party libraries.

1. Autocomplete(counts, k): counts maps each word to how often it was
   searched. suggest(prefix) returns up to k stored words that start with
   prefix: the highest count first, ties in alphabetical order.
   bump(word) adds 1 to a word's count (a new word starts at 1).

       a = Autocomplete({"car": 5, "card": 9, "care": 2, "cat": 9, "dog": 4}, k=2)
       a.suggest("ca")   -> ["card", "cat"]     (9 and 9: alphabetical)
       a.suggest("car")  -> ["card", "car"]
       a.suggest("x")    -> []
       a.bump("care"); a.bump("care"); a.bump("care"); a.bump("care")
       a.suggest("car")  -> ["card", "care"]    (care is now 6)

2. RouteTable: add(cidr, hop) stores an IPv4 route such as "10.1.0.0/16".
   The address part never has bits set past the prefix length. Adding the
   same prefix again replaces its hop. lookup(ip) returns the hop of the
   longest stored prefix that matches the address, or None.

       rt = RouteTable()
       rt.add("0.0.0.0/0", "default"); rt.add("10.0.0.0/8", "A")
       rt.add("10.1.0.0/16", "B")
       rt.lookup("10.1.2.3")  -> "B"   (both /8 and /16 match: /16 is longer)
       rt.lookup("10.2.0.1")  -> "A"
       rt.lookup("8.8.8.8")   -> "default"

3. max_xor_pair(nums): the largest a ^ b over two different positions of
   nums. Every number is in 0 .. 2**31 - 1, and there are at least two.

       max_xor_pair([3, 10, 5, 25, 2, 8]) -> 28   (5 ^ 25)

Requirements
------------
- Autocomplete: suggest in O(L + k) for a prefix of length L, however many
  words share the prefix: keep each node's best k ready, don't search the
  subtree per call. bump in about O(L * k). Counts only ever go up.
- RouteTable: lookup in O(32) steps, however many routes are stored (walk
  the address's bits through a binary trie, remembering the last route you
  passed). add in O(prefix length).
- max_xor_pair: O(31 n), with a binary trie of the numbers' bits.

What the tests measure
----------------------
Every test runs under a 10 s cap; a trie passes each in about a second.
- Autocomplete: 200,000 suggest calls on one- and two-letter prefixes over
  30,000 words, mixed with 20,000 bumps. Searching the subtree per call
  visits thousands of nodes each time (over a minute in all).
- RouteTable: 20,000 routes and 100,000 lookups. Checking every route per
  lookup is 2 billion checks.
- max_xor_pair: 50,000 numbers. Trying every pair is 1.25 billion XORs.

Before you code (say it out loud)
---------------------------------
1. Autocomplete: when a word's count goes up, which nodes' top-k lists can
   change? Why is that easy when counts only grow, and hard if they could
   shrink?
2. RouteTable: you walk 10.1.2.3 down the trie. Why can't you stop at the
   first route you meet? What do you return if you fall off the trie?
3. max_xor_pair: for each number, why do you try the opposite bit first,
   starting from the highest bit?

Run:  pytest -k trie_patterns
"""


class Autocomplete:
    def __init__(self, counts: dict[str, int], k: int):
        raise NotImplementedError

    def suggest(self, prefix: str) -> list[str]:
        raise NotImplementedError

    def bump(self, word: str) -> None:
        raise NotImplementedError


class RouteTable:
    def __init__(self):
        raise NotImplementedError

    def add(self, cidr: str, hop: str) -> None:
        raise NotImplementedError

    def lookup(self, ip: str) -> str | None:
        raise NotImplementedError


def max_xor_pair(nums: list[int]) -> int:
    raise NotImplementedError
