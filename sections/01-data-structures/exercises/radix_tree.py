"""
Radix tree (compressed trie)
Topic: 01.06  |  Priority: P1

Problem
-------
Build section 9 of the chapter: a trie where every chain of single-child
nodes is squeezed into one edge labelled with a whole string. Inserting
may split an edge in two; deleting may merge two edges back into one.

    r = RadixTree()
    r.insert("test")    edges:  "test"
    r.insert("team")    edges:  "te" -> {"st", "am"}          (split "test")
    r.insert("tea")     edges:  "te" -> {"st", "a" -> {"m"}}   (split "am")
    r.contains("te")    -> False   (a node, but no word ends there)
    r.starts_with("tes") -> True   (the prefix ends in the middle of "st")

    r.structure() -> (False, {"te": (False, {"st": (True, {}),
                                             "a":  (True, {"m": (True, {})})})})

Requirements
------------
- insert(word), contains(word), starts_with(prefix): O(L) character
  comparisons for a string of length L. Duplicates are stored once; "" is
  a word like any other.
- delete(word) -> bool: True if it was stored. Afterwards the tree must be
  compressed again: remove a leaf that is no longer a word, and merge a
  node that is not a word and has one child into that child.
- __len__: the number of stored words. node_count(): nodes including the
  root.
- structure(): the tree as nested tuples, (is_word, {edge_label: child}),
  starting at the root. The tests read it to check the shape.

The shape rules the tests check after every change:
- every edge label is non-empty, and no two edges out of a node start with
  the same character;
- every node except the root is a word or has at least two children;
- the labels along the paths spell exactly the stored words.
So a plain one-letter-per-edge trie fails, and so does a delete that forgets
to merge. With those rules, n words need at most 2n + 1 nodes.

What the tests measure
----------------------
- The shape rules above, after each of thousands of random inserts and
  deletes.
- 20,000 pseudo-words: node_count() <= 2n + 1, and well below the plain
  trie's count.
- 20,000 inserts and 100,000 lookups under a 10 s cap.

Before you code (say it out loud)
---------------------------------
1. Inserting "team" next to the edge "test": where exactly do you split,
   and what does the new middle node hold?
2. starts_with("tes") stops halfway along the edge "st". Why is that a
   yes, without looking further down?
3. After a delete, which one or two nodes might need merging, and why
   never more?
4. Why can't a radix tree have more than about 2n nodes?

Run:  pytest -k radix_tree
"""


class RadixTree:
    def __init__(self):
        raise NotImplementedError

    def insert(self, word: str) -> None:
        raise NotImplementedError

    def contains(self, word: str) -> bool:
        raise NotImplementedError

    def starts_with(self, prefix: str) -> bool:
        raise NotImplementedError

    def delete(self, word: str) -> bool:
        raise NotImplementedError

    def node_count(self) -> int:
        raise NotImplementedError

    def structure(self) -> tuple:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
