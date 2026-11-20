"""
A* on a grid
Topic: 02.08  |  Priority: P1

Problem
-------
A map as a list of strings. '#' is a wall. A digit '1'..'9' is open ground,
and the digit is the cost of stepping ONTO that cell (mud costs more than
road). You move up, down, left or right. The cost of a route is the sum of
the costs of the cells it enters; the start cell itself is free.

    grid = ["1991",
            "1111"]
    astar(grid, (0, 0), (0, 3))   ->  5     (down 1, along the bottom 1+1+1, up 1)
                                            (straight along the top costs 9+9+1 = 19)

Function
--------
astar(grid, start, goal) -> int
    The least cost from start to goal, or -1 if goal can't be reached.
    start and goal are (row, col) tuples of open cells; start == goal gives 0.
    Use A* with a heuristic that never overestimates the remaining cost.
    Target: O(E log V) in the worst case, like Dijkstra, but on an open map
    it should look at little more than the cells along the answer.

How the tests measure your work
-------------------------------
Each row is a list that counts every cell you read and refuses writes.
On an open 200 x 200 map with start and goal 189 steps apart in one row,
the budget is 20 reads per step of the answer (about 3,800, under 10% of
the map). Plain Dijkstra spreads out in a diamond and reads tens of
thousands of cells. Copying the grid first reads all 40,000. Read cells
when you need them, and keep your own record of what you've seen.
Random weighted maps check the answer is the true least cost, so a
heuristic that can overestimate (say, Manhattan distance x 5) fails.

Before you code (say it out loud)
---------------------------------
1. f = g + h. What do g and h mean here, and which one does Dijkstra use?
2. Every step costs at least 1. Why does that make Manhattan distance a
   safe heuristic? What would make it unsafe?
3. Why is it safe to stop the moment the goal comes out of the heap?
4. On an open map with start and goal on a diagonal, many cells tie on f.
   How could a tie-break toward larger g (smaller h) help?

Run:  pytest -k astar_grid
"""


def astar(grid: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int:
    raise NotImplementedError
