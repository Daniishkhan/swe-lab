"""
Clone a graph
Topic: 01.05  |  Priority: P0

Problem
-------
A graph is stored as node objects. Each Node has a `val` and a list
`neighbors` of other Nodes (a directed edge to each). Given one node,
return a deep copy of everything reachable from it: a new Node for every
original node, with the same val, whose neighbors list holds the copies of
the original's neighbors, in the same order.

    a = Node(1); b = Node(2)
    a.neighbors = [b]; b.neighbors = [a, b]     # a cycle and a self-loop
    c = clone(a)
    c is not a, c.val == 1
    c.neighbors[0].val == 2
    c.neighbors[0].neighbors[0] is c            # the cycle is copied, not unrolled
    c.neighbors[0].neighbors[1] is c.neighbors[0]

clone(None) returns None. Vals need not be unique, so they can't identify
a node: the node object itself does.

Requirements
------------
- O(V + E) time for V reachable nodes and E edges.
- Exactly one new Node per original node, and the copy shares no Node with
  the original. Don't change the original.
- No recursion: the tests use a 100,000-node chain, far past Python's
  recursion limit of about 1,000. No copy.deepcopy either (it recurses, and
  it's the answer).

What the tests measure
----------------------
They count every Node created, check the copy node by node against the
original, and time-cap a 100,000-node graph. Looking up "have I copied this
node yet?" by scanning the copies made so far is O(V^2) and runs out of
time.

Before you code (say it out loud)
---------------------------------
1. When you meet a neighbor, how do you know in O(1) whether it already has
   a copy, and how do you find that copy?
2. When is a node's copy created, and when are its neighbors filled in?
   Why does a cycle not loop forever?

Run:  pytest -k clone_graph
"""


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

    def __repr__(self):
        return f"Node({self.val!r})"


def clone(node: Node | None) -> Node | None:
    raise NotImplementedError
