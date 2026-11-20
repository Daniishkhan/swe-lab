"""
Back-of-the-envelope capacity calculator
Topic: 02.16  |  Priority: P2

Problem
-------
Sections 2 to 6 of the chapter, as code you can trust in a system design
mock. Given a few facts about a service, turn them into requests per second,
storage, bandwidth, machines and requests in flight, with the units right.

    in_flight(20_000, 0.05)            -> 1000.0   # Little's law: L = lambda * W
    machines_needed(180_000, 2_000, 0.6) -> 150    # 180,000 / (2,000 * 0.6)
    machines_needed(270, 100, 0.3)     -> 9        # not 10: see "rounding" below

    spec = {
        "dau": 100_000_000,          # daily active users
        "reads_per_user": 50,        # reads per user per day
        "writes_per_user": 2,        # writes per user per day
        "read_bytes": 20_000,        # bytes sent back per read
        "write_bytes": 1_000,        # bytes stored per write (one copy)
        "peak_factor": 3,            # busiest moment / daily average
        "replicas": 3,               # copies of every stored byte
        "years": 5,                  # how long we keep the data
        "per_machine_qps": 2_000,    # requests/second one machine can serve
        "utilization": 0.6,          # run machines at most 60% busy
        "latency_s": 0.05,           # seconds each request spends inside
    }
    estimate(spec) -> {
        "avg_qps":          60185.185...,     # 52 * 1e8 / 86,400
        "peak_qps":         180555.55...,
        "peak_read_qps":    173611.11...,
        "peak_write_qps":   6944.44...,
        "storage_bytes":    1.095e15,         # about 1.1 PB
        "peak_egress_bits": 2.777...e10,      # bits per second, about 28 Gbit/s
        "machines":         151,
        "peak_in_flight":   9027.77...,
    }

Requirements
------------
- in_flight(arrival_rate, seconds_in_system) -> float. Little's law.
- machines_needed(peak_qps, per_machine_qps, utilization) -> int: the
  smallest whole number of machines k with k * per_machine_qps * utilization
  >= peak_qps, and at least 1. Raise ValueError if per_machine_qps <= 0 or
  utilization is not in (0, 1].
  Rounding: 270 / 100 / 0.3 is 9.000000000000002 in Python, so a plain
  math.ceil says 10 (and 39.2 / (7 * 0.7) overshoots 8 the same way).
  The rule: if the ratio r is within r * 1e-12 of a whole number n, the
  answer is n; otherwise it is math.ceil(r). Keep the tolerance that tight:
  1e-9 of 1.5 billion machines is 1.5 machines, wide enough to round a
  real 0.4 of a machine away. (Fraction(0.3) and Decimal(0.3) don't dodge
  this: they hold the float's exact value, a hair under 0.3.)
- estimate(spec) -> dict with exactly the eight keys above. A day is 86,400
  seconds and a year is 365 days. Storage counts every replica. Egress is
  the peak read traffic in BITS per second (network links are sold in bits).
  "machines" serves all peak traffic (reads and writes). "peak_in_flight" is
  Little's law at the peak. Don't modify spec.
- Everything is O(1): arithmetic on the inputs, never a loop over users,
  days or requests.

What the tests check
--------------------
Each key against values worked out by hand (relative error 1e-9), the
86,400 / 365 / x8 unit traps one at a time, the rounding case above, one
machine pool for reads and writes together (not rounded up separately), the
errors, an unchanged spec, and a spec with 10^15 users under a 2-second cap.

Before you code (say it out loud)
---------------------------------
1. Why does doubling latency double the requests in flight, even though
   the traffic didn't change?
2. Why plan machines for the peak at 60% utilization, not the average at
   100%?
3. Your answer says 28 Gbit/s. Is that a lot for one data center? For one
   machine with a 25 Gbit/s network card?

Run:  python3 -m pytest -k capacity_estimate
"""


def in_flight(arrival_rate, seconds_in_system):
    raise NotImplementedError


def machines_needed(peak_qps, per_machine_qps, utilization):
    raise NotImplementedError


def estimate(spec):
    raise NotImplementedError
