"""
Trie (prefix tree) for autocomplete
Topic: 01.06  |  Priority: P1

Problem
-------
Store words so you can answer prefix questions quickly.

Requirements
------------
- insert(word)
- contains(word) -> True only for exact inserted words.
- starts_with(prefix) -> True if any inserted word has this prefix.
- words_with_prefix(prefix, limit=None) -> matching words in lexicographic order,
  at most `limit` of them if given.
- Inserting the same word twice is harmless.

Before you code (say it out loud)
---------------------------------
1. Cost of a lookup in a trie vs a hash set vs a sorted list + binary search?
2. Why do you need an "end of word" marker?
3. How would a radix tree compress this? Where are radix trees used (routers)?

Run:  pytest -k trie
"""


class Trie:
    def __init__(self):
        raise NotImplementedError

    def insert(self, word: str) -> None:
        raise NotImplementedError

    def contains(self, word: str) -> bool:
        raise NotImplementedError

    def starts_with(self, prefix: str) -> bool:
        raise NotImplementedError

    def words_with_prefix(self, prefix: str, limit: int | None = None) -> list[str]:
        raise NotImplementedError
