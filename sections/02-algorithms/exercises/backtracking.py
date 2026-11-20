"""
Backtracking: generate, prune, and search
Topic: 02.06  |  Priority: P0  |  Chapter: concepts/backtracking.html (exercises 4-7)

The tests hand you values that COUNT the work you do on them: comparisons,
hashes and function calls for exercise 4, additions, subtractions and comparisons for 5 and 7,
and cell reads for 6. A right answer is not enough: a search that explores
branches it could have cut fails, with a message saying how much work it did.
Don't use itertools in this file; the point is to build the search yourself.
Numbers below match the exercise numbers in the chapter.

4. unique_permutations(nums) -> list[list]
   Every DISTINCT ordering of nums, which may contain repeats.
   [1, 1, 2] -> [[1, 1, 2], [1, 2, 1], [2, 1, 1]] (any order of the lists).
   [] -> [[]]. Don't change the input list.
   Making all n! orderings and throwing away repeats afterwards is too slow:
   for 12 numbers with only 2,970 distinct orderings, that's 479 million
   orderings. Never build the same ordering twice. Section 8's rule for
   subsets ("skip a value equal to the one you just tried at this depth")
   needs one more thought for permutations, because a permutation's loop
   starts at index 0 every time.

5. combination_sum(candidates, target) -> list[list[int]]
   candidates are distinct positive ints, in any order; target >= 1. Return
   every combination of candidates that adds up to target, where each
   candidate may be used any number of times. [2, 2, 3] and [3, 2, 2] are the
   same combination: return it once.
   ([2, 3, 6, 7], 7) -> [[2, 2, 3], [7]]. ([2], 1) -> [].
   Two cuts are tested: never build two orders of the same combination
   (section 6), and once a candidate is bigger than what's left of the
   target, don't try it or anything bigger (section 7). Carry what's left of
   the target down the recursion instead of re-adding the path at every node.

6. word_search(board, word) -> bool
   board is a non-empty grid of single letters: board[r][c]. word is
   non-empty. Can you spell word by walking from cell to cell up, down, left
   or right, using each cell at most once in the walk?
   board = [["A","B","C","E"],
            ["S","F","C","S"],
            ["A","D","E","E"]]
   "ABCCED" -> True, "SEE" -> True, "ABCB" -> False (the B cell can't be
   reused). The board must look exactly the same when you return: if you
   mark cells while you search, un-mark them. The tests count every cell you
   read. Stop a walk as soon as a letter doesn't match. And one cheap pass
   over the board before searching can rule out a hopeless word: a board with
   one B can't spell a word with two Bs, however you walk.

7. can_partition_k(nums, k) -> bool
   nums is a non-empty list of positive ints, 1 <= k <= len(nums). Can you
   split nums into k groups with equal sums, using every number exactly once?
   ([4, 3, 2, 3, 5, 2, 1], 4) -> True: (5), (1, 4), (2, 3), (2, 3).
   ([1, 2, 3, 4], 3) -> False. Don't change the input list.
   The tests give you inputs with no answer, where trying every way to deal
   the numbers into k groups (k^n of them) never finishes. Cut three kinds
   of branch (section 7): a group that would go over its share (skip it);
   the order you place numbers in (place the biggest first: they run out of
   room soonest, so dead branches die near the top of the tree); and mirror
   images (if a number failed in one empty group, it fails in every other
   empty group too, so try only one empty group).

Before you code (say it out loud)
---------------------------------
For each one: draw the top two levels of the decision tree. What is one
choice? What is the path, and where is the un-choose? Roughly how many nodes
does the tree have before pruning, and which cut removes the most?

Run:  python3 -m pytest -k backtracking
"""


def unique_permutations(nums: list) -> list:
    raise NotImplementedError


def combination_sum(candidates: list, target: int) -> list:
    raise NotImplementedError


def word_search(board: list, word: str) -> bool:
    raise NotImplementedError


def can_partition_k(nums: list, k: int) -> bool:
    raise NotImplementedError
