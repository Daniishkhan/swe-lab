"""
Exploring graphs: shortest paths, islands, exits, cycles, build order
Topic: 02.05  |  Priority: P0  |  Chapter: concepts/bfs-dfs.html (exercises 4-8)

The tests count your work, not just your answers:
  - Graph nodes count every time they are hashed (each dict or set lookup,
    insert and `in` check). The budget is 20 per node plus 20 per edge
    (in an undirected graph, 20 per neighbour-list entry).
  - Grids count every cell you read. The budget is 10 reads per cell.
So a correct but slow solution fails. Everything here is O(V + E), or
O(rows * cols) for a grid. Use collections.deque for queues: list.pop(0)
shifts the whole list every time.

Graphs are dicts: graph[node] is the list of node's neighbours (in a directed
graph, the nodes it points to). Every node is a key, even with an empty list.
Nodes can be any hashable value (strings in the examples). The test's nodes
are equal only to themselves and can't be sorted, so don't sort them.

Grids are lists of rows; grid[r][c] is one character. Rows may be strings or
lists, so only index them (grid[r][c], len(grid), len(grid[0])), and never
write to the grid: keep your own visited marks.

Numbers below match the exercise numbers in the chapter.

4. shortest_path(graph, start, goal) -> list | None
   Undirected, unweighted. Return the nodes along one shortest path,
   [start, ..., goal], both ends included. [start] when start == goal. None
   when goal can't be reached.
     graph = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A", "D"],
              "D": ["B", "C", "E"], "E": ["D"]}
     shortest_path(graph, "A", "E") -> ["A", "B", "D", "E"]  (or via "C")
   Section 4 shows how BFS finds the distance. Getting the path itself is
   your job: remember who discovered whom, then walk back from the goal.

5. count_islands(grid) -> int
   grid[r][c] is "1" (land) or "0" (water). Land cells that touch up, down,
   left or right (not diagonally) are one island. Return how many islands.
     ["11000",
      "11000",
      "00100",
      "00011"]  -> 3
   One test island winds through 7,380 cells: a recursive flood fill goes
   that many calls deep, and Python stops at about 1,000 (section 5).

6. steps_to_exit(grid) -> list[list[int]]
   grid[r][c] is "#" (wall), "E" (exit) or "." (floor). Return a table of the
   same shape: for each floor cell, the fewest up/down/left/right steps to
   the NEAREST exit; 0 on exits; -1 on walls and on floor cells that can't
   reach any exit.
     ["E..#",          [[ 0,  1,  2, -1],
      "..#.",    ->     [ 1,  2, -1,  2],
      "#...",           [-1,  3,  2,  1],
      "...E"]           [ 3,  2,  1,  0]]
   The test has 300 exits on an 80 x 80 grid. A BFS from each exit (or from
   each cell) reads every cell hundreds of times. Section 9's first "Go deeper"
   box shows how to do it in ONE search.

7. find_cycle(graph) -> list | None
   Directed. Return one cycle as a list of distinct nodes [v0, v1, ..., vk]
   where v0->v1, v1->v2, ..., vk->v0 are all edges. A self-loop v->v is [v].
   None if the graph has no cycle.
     {"A": ["B"], "B": ["C"], "C": ["A"]}            -> ["A", "B", "C"] (any rotation)
     {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []} -> None
   A plain visited set gets the second one wrong (section 7). One test is a
   cycle through 5,000 nodes, so a recursive DFS needs a raised recursion
   limit or, better, your own stack.

8. semester_plan(courses, prereqs) -> list[list] | None
   prereqs holds (before, after) pairs: before must be passed in an EARLIER
   semester than after. Each semester you take every course whose
   prerequisites are all passed. Return the semesters in order, each a list
   of courses (any order inside a semester), or None if some course can
   never be taken. The same pair may appear twice.
     courses = ["intro", "data", "algo", "web", "ml"]
     prereqs = [("intro", "data"), ("intro", "web"), ("data", "algo"),
                ("data", "ml"), ("algo", "ml")]
     -> [["intro"], ["data", "web"], ["algo"], ["ml"]]
   Section 8 shows Kahn's algorithm for one order. Here you need the order
   in rounds. Rescanning every course each semester is O(V * semesters):
   the test's 3,000-semester chain fails it.

Before you code (say it out loud)
---------------------------------
For each one: BFS or DFS, and why? What goes in the visited set, and when
do you mark it? What is V and what is E, and why is the total O(V + E)?
What happens on an empty input, a single node, and a cycle?

Run:  python3 -m pytest -k graphs
"""
from collections import deque  # noqa: F401  (you'll want it for BFS)


def shortest_path(graph: dict, start, goal) -> list | None:
    raise NotImplementedError


def count_islands(grid: list) -> int:
    raise NotImplementedError


def steps_to_exit(grid: list) -> list[list[int]]:
    raise NotImplementedError


def find_cycle(graph: dict) -> list | None:
    raise NotImplementedError


def semester_plan(courses: list, prereqs: list) -> list[list] | None:
    raise NotImplementedError
