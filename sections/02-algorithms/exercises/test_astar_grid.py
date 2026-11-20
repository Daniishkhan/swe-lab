import random
import signal

import pytest

from astar_grid import astar


class TooMuchWork(AssertionError):
    pass


class Row(list):
    """One map row. Counts every cell read and refuses writes."""

    reads = 0
    limit = None

    def _tick(self, k=1):
        Row.reads += k
        if Row.limit is not None and Row.reads > Row.limit:
            raise TooMuchWork(
                f"over {Row.limit:,} cell reads: is the search spreading in every direction "
                "(Dijkstra) instead of heading for the goal, or copying the whole map?"
            )

    def __getitem__(self, i):
        v = list.__getitem__(self, i)
        self._tick(len(v) if isinstance(i, slice) else 1)
        return v

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __contains__(self, x):
        self._tick(len(self))
        return list.__contains__(self, x)

    def __reversed__(self):
        for i in range(len(self) - 1, -1, -1):
            yield self[i]

    def copy(self):  # list.copy and friends would read every cell uncounted
        self._tick(len(self))
        return list(list.__iter__(self))

    def index(self, *args):
        self._tick(len(self))
        return list.index(self, *args)

    def count(self, x):
        self._tick(len(self))
        return list.count(self, x)

    def __repr__(self):
        self._tick(len(self))
        return list.__repr__(self)

    def __setitem__(self, i, v):
        raise TypeError("don't change the map: keep your own records")


def counted(rows, limit=None):
    Row.reads, Row.limit = 0, limit
    return [Row(r) for r in rows]


@pytest.fixture(autouse=True)
def time_limit():
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over the 10 s time cap")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
        Row.limit = None


def random_map(seed, rows, cols, wall_p, mud_p):
    """A seeded map. Uses only rnd.random(), whose sequence is the same on every Python 3."""
    rnd = random.Random(seed)
    grid = []
    for _ in range(rows):
        row = ""
        for _ in range(cols):
            x = rnd.random()
            if x < wall_p:
                row += "#"
            elif x < wall_p + mud_p:
                row += str(2 + int(rnd.random() * 8))  # mud: 2..9
            else:
                row += "1"
        grid.append(row)
    open_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] != "#"]
    start = open_cells[int(rnd.random() * len(open_cells))]
    goal = open_cells[int(rnd.random() * len(open_cells))]
    return grid, start, goal


# ---------------------------------------------------------------------------
# Small hand-made maps
# ---------------------------------------------------------------------------
def test_example():
    assert astar(counted(["1991", "1111"]), (0, 0), (0, 3)) == 5


def test_start_is_goal():
    assert astar(counted(["5"]), (0, 0), (0, 0)) == 0


def test_start_cell_is_free_and_goal_cell_is_paid():
    assert astar(counted(["91119"]), (0, 0), (0, 4)) == 1 + 1 + 1 + 9


def test_walled_off_goal():
    grid = ["11#11",
            "11#11",
            "11#11"]
    assert astar(counted(grid), (1, 0), (1, 4)) == -1


def test_cheap_detour_beats_short_mud():
    grid = ["1111111",
            "1999991",
            "1111111"]
    # The straight row-1 route costs 9*5 + 1 = 46; around the edge costs 8.
    assert astar(counted(grid), (1, 0), (1, 6)) == 8


def test_maze_that_points_the_wrong_way():
    # The goal is right next door through the wall; the only way round is long.
    grid = ["11111111",
            "1######1",
            "1#1111#1",
            "1#1##1#1",
            "1#1#11#1",
            "1#1#####",
            "11111111"]
    # In, out to the left, down, along the bottom, up the left side, across the top, down: 29 steps.
    assert astar(counted(grid), (4, 4), (4, 7)) == 29


# ---------------------------------------------------------------------------
# Random weighted maps. Expected answers were computed offline with two
# independent searches, and hard-coded here.
# ---------------------------------------------------------------------------
SMALL_ANSWERS = [5, -1, 15, 41, 17, -1, 19, 17, 12, 43, 0, 22, -1, 21, 13, -1, 15, 2, 0, 5,
                 1, -1, 12, 20, 11, 21, 17, 8, 19, 38, -1, -1, 8, 12, 11, 15, 16, 3, 5, 48,
                 -1, 18, 3, 24, -1, 14, -1, 13, 0, -1, 8, 27, -1, 35, 16, 21, 23, 30, 25, 15]


def test_random_small_weighted_maps():
    for seed, want in enumerate(SMALL_ANSWERS):
        grid, s, t = random_map(seed, 4 + seed % 5, 4 + (seed * 3) % 6, 0.25, 0.5)
        got = astar(counted(grid), s, t)
        assert got == want, f"seed {seed}: map {grid}, start {s}, goal {t}: got {got}, want {want}"


def test_big_weighted_map():
    grid, s, t = random_map(1000, 120, 160, 0.2, 0.4)
    assert (s, t) == ((110, 26), (31, 135))
    assert astar(counted(grid), s, t) == 334


# ---------------------------------------------------------------------------
# Open maps: A* should head for the goal, not flood the map
# ---------------------------------------------------------------------------
def open_map(rows, cols):
    return ["1" * cols for _ in range(rows)]


def test_open_map_reads_a_corridor_not_a_diamond():
    s, t = (100, 5), (100, 194)
    answer = 189
    grid = counted(open_map(200, 200), limit=20 * answer)
    assert astar(grid, s, t) == answer


def test_open_map_other_direction_and_column():
    s, t = (190, 60), (12, 60)
    answer = 178
    grid = counted(open_map(200, 120), limit=20 * answer)
    assert astar(grid, s, t) == answer


def test_wall_forces_a_detour():
    # A wall across rows 50..150 of column 100: go round its end, 51 up, 51 down.
    rows = open_map(200, 200)
    rows = [r[:100] + ("#" if 50 <= i <= 150 else "1") + r[101:] for i, r in enumerate(rows)]
    assert astar(counted(rows), (100, 5), (100, 194)) == 189 + 2 * 51
