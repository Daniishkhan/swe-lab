"""
Consistent hashing ring with virtual nodes and replicas
Topic: 02.15  |  Priority: P1

Problem
-------
Build sections 3, 6, 8 and 9 of the chapter: a hash ring that maps keys
(cache keys, user ids) to nodes (servers), so that adding or removing a node
moves only about 1/N of the keys, and only the keys that have to move.

    ring = ConsistentHashRing(vnodes=100)
    for name in ["cache-a", "cache-b", "cache-c"]:
        ring.add_node(name)
    ring.get_node("user:42")        -> "cache-b"   (whichever owns that spot)
    ring.get_nodes("user:42", 2)    -> ["cache-b", "cache-a"]   (2 replicas)
    ring.add_node("cache-d")        # about 1/4 of keys move, all to cache-d

Requirements
------------
- stable_hash(text) -> int in range(2**64), the same in every process and
  on every machine. Build it from hashlib (md5, sha1 or blake2b and
  int.from_bytes). Never Python's built-in hash() on a str: it is salted
  with a random seed per process (PYTHONHASHSEED), so two app servers would
  disagree about where every key lives. The tests run your code in two
  processes with different seeds and compare.

- ConsistentHashRing(vnodes=100, hash_fn=stable_hash)
  - Node `name` gets `vnodes` points on the ring. Point i (i = 0 .. vnodes-1)
    sits at position hash_fn(f"{name}#{i}"). Use exactly this label: the
    tests check your owners against a brute force that uses it.
  - A key sits at position hash_fn(key).
  - add_node(name): ValueError if already present. Calls hash_fn exactly
    `vnodes` times (one per point; never rehash the nodes already there).
  - remove_node(name): KeyError if absent. Calls hash_fn at most `vnodes`
    times (zero if you remember each node's points).
  - get_node(key): the node owning the first point clockwise from the key:
    the smallest position >= hash_fn(key), wrapping around to the smallest
    position overall if there is none. A point exactly at the key's
    position owns it. LookupError if the ring is empty. Calls hash_fn once.
    O(log P) for P points: a sorted list of positions plus bisect.
  - get_nodes(key, k): keep walking clockwise from that same point and
    return the first k DISTINCT nodes, in the order you meet them (a node's
    other virtual points are skipped). If the ring has fewer than k nodes,
    return all of them. LookupError if empty. Calls hash_fn once. Stop
    walking as soon as you have k nodes.
  - If two points land on exactly the same position (practically never with
    64-bit hashes), either may win.

What the tests measure
----------------------
- Exact owners and replica lists on a toy clock (hash_fn is a dict lookup
  on 0..99), including the wraparound and "a point exactly at the key owns
  it", for get_nodes as well as get_node.
- Your owners match a brute force (a linear scan over every point) for
  random rings, and get_nodes matches a brute-force clockwise walk.
  get_nodes must keep walking past however many points of one node come
  in a row (a toy ring puts 300 of them back to back).
- Adding an 11th node to 10 (vnodes=100) moves between 5% and 16% of
  20,000 keys (1/11 = 9.1% expected), and every moved key moves to the new
  node. Removing a node moves only that node's keys.
- With vnodes=200, 10 nodes and 20,000 keys, the busiest node holds less
  than 1.35x the average and the quietest more than 0.65x.
- hash_fn is wrapped in a counter: get_node and get_nodes may call it once,
  add_node exactly vnodes times, remove_node at most vnodes times.
- A ring of 200 nodes x 500 vnodes (100,000 points) answers 50,000
  get_node calls and 150,000 get_nodes(key, 3) calls under a 20 s cap per
  test. A linear scan over the points is about 25,000x slower, and so is
  copying or slicing the point list on every call (points[i:] + points[:i]
  reads all 100,000 points too).
- stable_hash gives the same numbers in two processes with different
  PYTHONHASHSEED values, and spreads "key-0", "key-1", ... evenly.

Before you code (say it out loud)
---------------------------------
1. With hash(key) % N, what fraction of keys move when N goes from 4 to 5?
   From N to N + 1? Why?
2. On the ring, which keys move when you add a node? Where do they go?
3. Why do virtual nodes even out the load? How does the spread shrink as
   vnodes grows (1, 100, 10,000)?
4. In get_nodes, why must you skip points that belong to a node you
   already picked?

Run:  pytest -k consistent_hash
"""


def stable_hash(text: str) -> int:
    raise NotImplementedError


class ConsistentHashRing:
    def __init__(self, vnodes: int = 100, hash_fn=stable_hash):
        raise NotImplementedError

    def add_node(self, name: str) -> None:
        raise NotImplementedError

    def remove_node(self, name: str) -> None:
        raise NotImplementedError

    def get_node(self, key: str) -> str:
        raise NotImplementedError

    def get_nodes(self, key: str, k: int) -> list[str]:
        raise NotImplementedError
