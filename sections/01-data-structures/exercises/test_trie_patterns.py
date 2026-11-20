import random
import signal

import pytest

from trie_patterns import Autocomplete, RouteTable, max_xor_pair


@pytest.fixture(autouse=True)
def time_limit():
    """A trie answers each test in about a second (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 10 s: is something scanning every word, route or pair?")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# 1. Autocomplete
def best(counts, prefix, k):
    hits = [w for w in counts if w.startswith(prefix)]
    return sorted(hits, key=lambda w: (-counts[w], w))[:k]


def test_autocomplete_example():
    a = Autocomplete({"car": 5, "card": 9, "care": 2, "cat": 9, "dog": 4}, k=2)
    assert a.suggest("ca") == ["card", "cat"]
    assert a.suggest("car") == ["card", "car"]
    assert a.suggest("x") == []
    assert a.suggest("dog") == ["dog"]
    assert a.suggest("") == ["card", "cat"]
    for _ in range(4):
        a.bump("care")
    assert a.suggest("car") == ["card", "care"]
    a.bump("cow")
    assert a.suggest("co") == ["cow"]
    for _ in range(9):
        a.bump("cow")
    assert a.suggest("c") == ["cow", "card"]


def test_autocomplete_edge_cases():
    a = Autocomplete({}, k=3)
    assert a.suggest("") == [] and a.suggest("a") == []
    a.bump("a")
    a.bump("")
    assert a.suggest("") == ["", "a"]
    b = Autocomplete({"x": 1, "xy": 1, "xyz": 1}, k=1)
    assert b.suggest("x") == ["x"] and b.suggest("xy") == ["xy"]


def test_autocomplete_random_against_brute():
    rng = random.Random(41)
    for _ in range(40):
        words = {"".join(rng.choice("abc") for _ in range(rng.randint(0, 4))) for _ in range(25)}
        counts = {w: rng.randint(1, 6) for w in words}
        k = rng.randint(1, 4)
        a = Autocomplete(dict(counts), k)
        for _ in range(80):
            if rng.random() < 0.4:
                w = "".join(rng.choice("abc") for _ in range(rng.randint(0, 4)))
                a.bump(w)
                counts[w] = counts.get(w, 0) + 1
            p = "".join(rng.choice("abc") for _ in range(rng.randint(0, 2)))
            assert a.suggest(p) == best(counts, p, k), (p, k)


def gen_words(n, seed):
    rng = random.Random(seed)
    syl = ["ca", "car", "co", "de", "do", "en", "er", "in", "ma", "mo", "ne", "on",
           "pa", "pre", "re", "sa", "st", "ta", "te", "to", "un", "x", "a", "e"]
    out = set()
    while len(out) < n:
        out.add("".join(rng.choice(syl) for _ in range(rng.randint(1, 5))))
    return sorted(out)


def test_autocomplete_is_fast_for_short_prefixes():
    rng = random.Random(42)
    words = gen_words(30_000, 43)
    counts = {w: int(1000 / (1 + rng.random() * 999)) for w in words}  # a few popular, many rare
    a = Autocomplete(dict(counts), k=5)
    prefixes = sorted({w[:1] for w in words}) + sorted({w[:2] for w in words})[:40]
    for p in prefixes:
        assert a.suggest(p) == best(counts, p, 5), p
    for i in range(200_000):  # walking a one-letter subtree visits thousands of nodes
        if i % 10 == 0:
            w = rng.choice(words)
            a.bump(w)
            counts[w] += 1
        a.suggest(rng.choice(prefixes))
    for p in prefixes:
        assert a.suggest(p) == best(counts, p, 5), p


# 2. RouteTable
def ip_to_int(ip):
    a, b, c, d = map(int, ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(x):
    return ".".join(str((x >> s) & 255) for s in (24, 16, 8, 0))


def brute_lookup(routes, ip):
    x, best_len, hop = ip_to_int(ip), -1, None
    for (net, plen), h in routes.items():
        mask = ((1 << plen) - 1) << (32 - plen)
        if x & mask == net and plen > best_len:
            best_len, hop = plen, h
    return hop


def test_routes_example():
    rt = RouteTable()
    assert rt.lookup("1.2.3.4") is None
    rt.add("10.0.0.0/8", "A")
    assert rt.lookup("10.200.0.1") == "A" and rt.lookup("11.0.0.0") is None
    rt.add("0.0.0.0/0", "default")
    rt.add("10.1.0.0/16", "B")
    assert rt.lookup("10.1.2.3") == "B"
    assert rt.lookup("10.2.0.1") == "A"
    assert rt.lookup("8.8.8.8") == "default"
    rt.add("10.1.2.3/32", "host")
    assert rt.lookup("10.1.2.3") == "host" and rt.lookup("10.1.2.4") == "B"
    rt.add("10.0.0.0/8", "A2")  # same prefix again: replace the hop
    assert rt.lookup("10.2.0.1") == "A2"


def test_routes_odd_lengths():
    rt = RouteTable()
    rt.add("192.168.0.0/23", "X")  # covers 192.168.0.* and 192.168.1.*
    rt.add("128.0.0.0/1", "top-half")
    assert rt.lookup("192.168.1.255") == "X"
    assert rt.lookup("192.168.2.0") == "top-half"
    assert rt.lookup("127.255.255.255") is None
    assert rt.lookup("255.255.255.255") == "top-half"


def random_routes(rng, n):
    routes = {}
    while len(routes) < n:
        plen = rng.choice([0, 1, 8, 12, 16, 16, 20, 24, 24, 24, 28, 32])
        net = rng.getrandbits(32) & ((((1 << plen) - 1) << (32 - plen)) if plen else 0)
        if rng.random() < 0.7:
            net = (net & 0x00FFFFFF) | (10 << 24)  # most routes inside 10.0.0.0/8, so they nest
            net &= (((1 << plen) - 1) << (32 - plen)) if plen else 0
        routes[(net, plen)] = f"hop{len(routes)}"
    return routes


def test_routes_random_against_brute():
    rng = random.Random(51)
    for _ in range(30):
        routes = random_routes(rng, rng.randint(1, 40))
        rt = RouteTable()
        for (net, plen), h in routes.items():
            rt.add(f"{int_to_ip(net)}/{plen}", h)
        for _ in range(100):
            if rng.random() < 0.5:
                (net, plen) = rng.choice(list(routes))
                x = net | (rng.getrandbits(32 - plen) if plen < 32 else 0)
            else:
                x = rng.getrandbits(32)
            ip = int_to_ip(x)
            assert rt.lookup(ip) == brute_lookup(routes, ip), ip


def test_routes_many():
    rng = random.Random(52)
    routes = random_routes(rng, 20_000)
    rt = RouteTable()
    for (net, plen), h in routes.items():
        rt.add(f"{int_to_ip(net)}/{plen}", h)
    keys = list(routes)
    ips = []
    for _ in range(100_000):  # checking all 20,000 routes per lookup: 2 billion checks
        net, plen = rng.choice(keys)
        ips.append(int_to_ip(net | (rng.getrandbits(32 - plen) if plen < 32 else 0)))
    got = [rt.lookup(ip) for ip in ips]
    for ip, g in zip(ips[:300], got[:300]):
        assert g == brute_lookup(routes, ip), ip
    assert all(g is not None for g in got)


# 3. max_xor_pair
def brute_xor(nums):
    return max(nums[i] ^ nums[j] for i in range(len(nums)) for j in range(i + 1, len(nums)))


def test_xor_examples():
    assert max_xor_pair([3, 10, 5, 25, 2, 8]) == 28
    assert max_xor_pair([0, 0]) == 0
    assert max_xor_pair([7, 7, 7]) == 0
    assert max_xor_pair([1, 2]) == 3
    assert max_xor_pair([2**31 - 1, 0]) == 2**31 - 1
    assert max_xor_pair([14, 70, 53, 83, 49, 91, 36, 80, 92, 51, 66, 70]) == 127


def test_xor_random_against_brute():
    rng = random.Random(61)
    for _ in range(200):
        nums = [rng.randrange(rng.choice([4, 64, 2**31])) for _ in range(rng.randint(2, 30))]
        assert max_xor_pair(nums) == brute_xor(nums), nums


def test_xor_many():
    # 49,999 numbers below 2**30 and one "special" number with bit 30 set. Any
    # pair without the special number has XOR below 2**30, and any pair with it
    # is at least 2**30, so the answer is the best partner for the special one.
    rng = random.Random(62)
    nums = [rng.randrange(2**30) for _ in range(49_999)]
    special = 2**30 + rng.randrange(2**30)
    nums.insert(rng.randrange(len(nums) + 1), special)
    want = max(special ^ x for x in nums if x != special)
    assert max_xor_pair(nums) == want  # trying all pairs: 1.25 billion XORs
