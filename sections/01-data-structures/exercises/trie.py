"""
Trie (prefix tree) for autocomplete
Topic: 01.06  |  Priority: P1

Problem
-------
Build sections 3 to 6 of the chapter: a trie that stores words and answers
prefix questions by walking one letter per step.

    t = Trie()
    for w in ["car", "card", "care", "cart", "cat", "do", "dog"]:
        t.insert(w)
    t.contains("car")            -> True
    t.contains("ca")             -> False   (a path, but no word ends there)
    t.starts_with("ca")          -> True
    t.count_prefix("car")        -> 4       (car, card, care, cart)
    t.words_with_prefix("car")   -> ["car", "card", "care", "cart"]
    t.words_with_prefix("", limit=2) -> ["car", "card"]
    t.delete("card")             -> True
    t.delete("card")             -> False   (already gone)
    len(t)                       -> 6

Requirements
------------
- insert(word): O(L) for a word of length L. Inserting a word twice is
  harmless (it is stored once). Any characters are allowed, and the empty
  string "" is a word like any other.
- contains(word): True only for words that were inserted (and not deleted).
- starts_with(prefix): True if at least one stored word starts with prefix.
  O(L).
- count_prefix(prefix): how many stored words start with prefix, in O(L),
  however many words that is. (Hint: each node keeps a number.)
- words_with_prefix(prefix, limit=None): the matching words in sorted
  (Python string) order, at most limit of them. It must stop as soon as it
  has limit words: cost O(L + the nodes it visits to find them), not the
  size of the whole subtree.
- delete(word): remove it and return True, or return False if it wasn't
  stored. Remove the nodes that no longer lead to any word, so memory
  goes back down.
- len(t): the number of stored words.
- No sorted(), list.sort() or bisect over the whole word list: the trie
  does the work. Sorting one node's children is fine.

What the tests measure
----------------------
Every test runs under a 10 s cap; a trie passes each in well under a second.
- 300,000 count_prefix calls on one- and two-letter prefixes over 40,000
  words: walking the subtree to count visits about 5,000 nodes per call,
  over a minute in all.
- 5,000 words_with_prefix("", limit=3) calls on 40,000 words: an early
  stop visits a few dozen nodes per call; collecting everything and then
  slicing visits all of the trie's ~106,000 nodes every time (over a minute).
- 100,000 rounds of contains and starts_with over 20,000 words: scanning a
  word list is 2 billion checks for each kind of call.
- Memory (tracemalloc): after deleting every word, at least 90% of the
  memory the inserts took must be freed. A delete that only clears the
  end-of-word mark frees almost nothing.

Before you code (say it out loud)
---------------------------------
1. Why does contains("ca") need an end-of-word mark, when the path c-a
   exists?
2. Where does sorted output come from, without ever calling sort?
3. What number does each node keep for count_prefix, and which nodes'
   numbers change on insert and on delete?
4. On delete, which nodes can you remove, and how do you know to stop?

Run:  pytest -k "test_trie and not trie_patterns"
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

    def count_prefix(self, prefix: str) -> int:
        raise NotImplementedError

    def words_with_prefix(self, prefix: str, limit: int | None = None) -> list[str]:
        raise NotImplementedError

    def delete(self, word: str) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
