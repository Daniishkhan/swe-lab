"""
Concurrent web crawler with worker pool and per-host concurrency cap
Topic: 03.05 03.07  |  Priority: P0

Directly rehearses Mock 4 (Anthropic / Google concurrency coding): crawl a web
graph concurrently with a global worker limit AND a per-host concurrency cap,
visiting every reachable URL at most once.

Function
--------
crawl(start_urls, fetch, max_workers=8, max_per_host=2) -> set[str]
    - start_urls: iterable of seed URLs (may be empty or contain duplicates).
    - fetch(url) -> iterable[str]: returns links found on `url`. May be slow
      (simulated network I/O) and may raise an exception on broken pages.
    - max_workers: maximum simultaneous `fetch` calls across all hosts (>= 1).
    - max_per_host: maximum simultaneous `fetch` calls to the SAME host
      (`urllib.parse.urlparse(url).netloc`) at any instant (>= 1).
    - Returns the set of all discovered URLs (including seeds and URLs whose
      fetch raised an exception—do not crash the crawl on one bad page, and
      never leak a per-host semaphore/permit when fetch raises!).
    - Raise ValueError if max_workers < 1 or max_per_host < 1.

What the tests measure
----------------------
- Completeness & deduplication: handles cycles and diamond graphs, calling
  fetch(url) at most ONCE per URL across all worker threads.
- Concurrency caps: tracks live simultaneous calls globally (<= max_workers)
  and per host (<= max_per_host).
- True parallelism: verifies peak concurrent fetches > 1 (a sequential crawler
  fails the test!).
- Exception resilience: a throwing page does not crash the crawl, hang worker
  threads, or leak per-host concurrency slots.

Before you code (say it out loud)
---------------------------------
1. When must a URL be added to `visited`—before scheduling it, or after
   `fetch(url)` returns? Why?
2. How do you know the crawl is finished when workers themselves push new URLs
   into the work queue? (Think: in-flight task counter / queue.task_done().)
3. What happens if 8 workers all pick URLs for slow-host.com when
   max_per_host == 2? Could that cause head-of-line blocking, and how do you
   prevent leaks on fetch exceptions?

Run:  python3 -m pytest -k concurrent_crawler
"""


def crawl(start_urls, fetch, max_workers=8, max_per_host=2):
    raise NotImplementedError
