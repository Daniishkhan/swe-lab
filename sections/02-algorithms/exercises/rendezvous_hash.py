"""
Rendezvous hashing (highest random weight)
Topic: 02.15  |  Priority: P2

Problem
-------
Build section 7 of the chapter. No ring this time: for each key, every node
gets a score, and the node with the highest score owns the key. Adding a
node only takes the keys it now wins; removing one hands each of its keys
to that key's second-highest scorer.

    rh = RendezvousHash(hash_fn)
    for name in ["cache-a", "cache-b", "cache-c"]:
        rh.add_node(name)
    rh.get_node("user:42")       -> "cache-c"   (highest score for this key)
    rh.get_nodes("user:42", 2)   -> ["cache-c", "cache-a"]   (top 2: replicas)

Requirements
------------
- RendezvousHash(hash_fn, nodes=()): hash_fn maps a str to an int (the
  tests pass a deterministic 64-bit hash). nodes: names to add right away.
- The score of node n for key k is hash_fn(f"{n}|{k}"). Use exactly this
  label: the tests compare with a brute force that uses it.
- Higher score wins. If two scores are equal, the larger node name wins
  (compare (score, name) pairs). With 64-bit hashes ties never happen;
  the toy-hash tests use them on purpose.
- add_node(name): ValueError if present.  remove_node(name): KeyError if
  absent. Neither calls hash_fn.
- get_node(key): the winner. LookupError if there are no nodes. Calls
  hash_fn exactly once per node: O(N) for N nodes.
- get_nodes(key, k): the k highest scorers, best first; all nodes if there
  are fewer than k. LookupError if there are no nodes. Also exactly one
  hash_fn call per node, even for big k: score each node once, then pick.

What the tests measure
----------------------
- Exact winners and orders on a toy hash, including the tie rule.
- Agreement with a brute force for random node sets.
- Adding an 11th node to 10 moves 6% to 13% of 20,000 keys (1/11 = 9.1%),
  all of them to the new node. Removing a node moves only its keys, and
  each one lands on the node that was its second choice before.
- With 10 nodes and no virtual nodes at all, every node gets within 15%
  of the average of 20,000 keys.
- hash_fn is wrapped in a counter: get_node and get_nodes(key, k) may call
  it at most N times per call. Picking the max k times, rescoring each
  time, costs k * N and fails.

Before you code (say it out loud)
---------------------------------
1. Why does adding a node never move a key between two old nodes?
2. When a node dies, where does each of its keys go? Why is that spread
   evenly without virtual nodes?
3. Each lookup costs N hashes. When is that fine, and when is the ring's
   O(log N) worth its extra memory and code?

Run:  pytest -k rendezvous_hash
"""


class RendezvousHash:
    def __init__(self, hash_fn, nodes=()):
        raise NotImplementedError

    def add_node(self, name: str) -> None:
        raise NotImplementedError

    def remove_node(self, name: str) -> None:
        raise NotImplementedError

    def get_node(self, key: str) -> str:
        raise NotImplementedError

    def get_nodes(self, key: str, k: int) -> list[str]:
        raise NotImplementedError
