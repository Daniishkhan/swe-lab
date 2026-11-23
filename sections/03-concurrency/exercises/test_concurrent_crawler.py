import threading
import time
from collections import defaultdict
from urllib.parse import urlparse

import pytest

from concurrent_crawler import crawl


def test_crawler_edges_and_validation():
    assert crawl([], lambda u: []) == set()
    with pytest.raises(ValueError):
        crawl(["https://a.com/1"], lambda u: [], max_workers=0)
    with pytest.raises(ValueError):
        crawl(["https://a.com/1"], lambda u: [], max_per_host=0)


def test_crawler_dedup_cycles_parallelism_and_caps():
    # Build 4 hosts x 6 pages = 24 pages with cycles & cross-host links
    hosts = ["h1.test", "h2.test", "h3.test", "h4.test"]
    graph = {}
    for hi, host in enumerate(hosts):
        for p in range(6):
            url = f"https://{host}/p{p}"
            next_same = f"https://{host}/p{(p + 1) % 6}"
            next_other = f"https://{hosts[(hi + 1) % len(hosts)]}/p{p}"
            graph[url] = [next_same, next_other, f"https://{host}/p0"]

    lock = threading.Lock()
    fetch_counts = defaultdict(int)
    active_total = 0
    peak_total = 0
    active_host = defaultdict(int)
    peak_host = defaultdict(int)

    def fetch(url):
        nonlocal active_total, peak_total
        host = urlparse(url).netloc
        with lock:
            fetch_counts[url] += 1
            active_total += 1
            peak_total = max(peak_total, active_total)
            active_host[host] += 1
            peak_host[host] = max(peak_host[host], active_host[host])
        try:
            time.sleep(0.03)
            return graph[url]
        finally:
            with lock:
                active_total -= 1
                active_host[host] -= 1

    seeds = ["https://h1.test/p0", "https://h1.test/p0", "https://h2.test/p0"]
    got = crawl(seeds, fetch, max_workers=6, max_per_host=2)

    assert got == set(graph.keys())
    assert all(cnt == 1 for cnt in fetch_counts.values()), f"duplicate fetches: {dict(fetch_counts)}"
    assert peak_total <= 6, f"exceeded max_workers=6 (saw {peak_total})"
    assert peak_total >= 3, f"crawler did not run in parallel (peak={peak_total})"
    for host, pk in peak_host.items():
        assert pk <= 2, f"exceeded max_per_host=2 on {host} (saw {pk})"


def test_crawler_survives_fetch_errors_without_leaking_permits():
    graph = {
        "https://a.test/root": ["https://a.test/bad1", "https://a.test/bad2", "https://a.test/good"],
        "https://a.test/good": ["https://a.test/leaf"],
        "https://a.test/leaf": [],
    }

    def fetch(url):
        time.sleep(0.01)
        if "bad" in url:
            raise ConnectionError(f"failed {url}")
        return graph[url]

    got = crawl(["https://a.test/root"], fetch, max_workers=4, max_per_host=1)
    assert got == {
        "https://a.test/root",
        "https://a.test/bad1",
        "https://a.test/bad2",
        "https://a.test/good",
        "https://a.test/leaf",
    }
