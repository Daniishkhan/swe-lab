"""
Python in-depth: data model, classic gotchas, decorators and context managers
Topic: 10.10  |  Priority: P0
Chapter: sections/10-code-quality-design-testing/concepts/python-idioms.html

Five drills targeting the exact Python subtleties that cause silent bugs in
DP tables, recursion, priority queues, memoization and resource cleanup.

Functions & Classes
-------------------
make_grid(rows, cols, fill=0) -> list[list]
    Return an independent rows x cols 2D list filled with `fill`.
    Mutating grid[0][0] must NOT change any other row (avoid [[fill]*cols]*rows).
    rows < 0 or cols < 0 raises ValueError.

append_log(entry, bucket=None) -> list
    Append `entry` to `bucket` (creating a fresh list if bucket is None) and
    return the list. Never use a mutable default argument like bucket=[].

PriorityTask(priority: int, seq: int, name: str)
    An immutable, hashable, orderable task object (great with @dataclass(frozen=True, order=True)):
      - Attributes: priority, seq, name
      - Ordered by (priority, seq, name) so heapq.heappush / heappop work even
        when two tasks share the same priority
      - Hashable and equality-comparable so tasks can be stored in sets and dicts
      - Immutable: attempting to assign t.priority = 99 raises AttributeError / FrozenInstanceError

memoize(fn) -> Callable
    A decorator that caches results of `fn` keyed by its positional arguments:
      - Preserves fn.__name__ and fn.__doc__ (use functools.wraps)
      - Calls fn at most once per unique args tuple
      - Correctly caches falsy results like None, 0, False, "" without recomputing

scoped_append(items, value) -> ContextManager
    A context manager (use @contextlib.contextmanager or __enter__/__exit__):
      - On enter: appends `value` to `items` and yields `items`
      - On exit: removes that appended item (items.pop()) EVEN IF an exception
        is raised inside the `with` block, and lets the exception propagate.

Before you code (say it out loud)
---------------------------------
1. Why does `grid = [[0] * 3] * 4` link all 4 rows, and why doesn't `[0] * 3`
   cause the same bug for ints?
2. Why does Python evaluate default function arguments at `def` time rather
   than call time?
3. In `memoize`, why is `if args in cache:` safer than `if cache.get(args):`?
4. In `scoped_append`, what happens if you forget `try ... finally` around `yield`?

Run:  python3 -m pytest -k py_internals
"""


def make_grid(rows, cols, fill=0):
    raise NotImplementedError


def append_log(entry, bucket=None):
    raise NotImplementedError


class PriorityTask:
    def __init__(self, priority, seq, name):
        raise NotImplementedError


def memoize(fn):
    raise NotImplementedError


def scoped_append(items, value):
    raise NotImplementedError
