import copy
import math
import signal

import pytest

from capacity_estimate import estimate, in_flight, machines_needed


@pytest.fixture(autouse=True)
def time_limit():
    """Every answer is a handful of multiplications (Unix only)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def boom(*_):
        raise TimeoutError("over 2 s: estimates are arithmetic, not a loop over users or requests")

    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(2)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def close(a, b, rel=1e-9):
    return math.isclose(a, b, rel_tol=rel, abs_tol=1e-12)


EXAMPLE = {
    "dau": 100_000_000,
    "reads_per_user": 50,
    "writes_per_user": 2,
    "read_bytes": 20_000,
    "write_bytes": 1_000,
    "peak_factor": 3,
    "replicas": 3,
    "years": 5,
    "per_machine_qps": 2_000,
    "utilization": 0.6,
    "latency_s": 0.05,
}

KEYS = {"avg_qps", "peak_qps", "peak_read_qps", "peak_write_qps",
        "storage_bytes", "peak_egress_bits", "machines", "peak_in_flight"}


# ---------- Little's law ----------

def test_in_flight_examples():
    assert close(in_flight(20_000, 0.05), 1000.0)
    assert close(in_flight(30 / 60, 20), 10.0)        # coffee shop: 0.5 people/min, 20 min each
    assert close(in_flight(0, 5.0), 0.0)
    assert close(in_flight(1e6, 2e-3), 2000.0)


# ---------- machines ----------

def test_machines_examples():
    assert machines_needed(180_000, 2_000, 0.6) == 150
    assert machines_needed(180_001, 2_000, 0.6) == 151
    assert machines_needed(1, 2_000, 0.6) == 1
    assert machines_needed(0, 2_000, 0.6) == 1          # a service always runs somewhere
    assert machines_needed(5_000, 1_000, 1.0) == 5
    assert isinstance(machines_needed(5_000, 1_000, 1.0), int)


def test_machines_float_rounding():
    # 270 / 100 / 0.3 == 9.000000000000002 in floating point,
    # and so is 39.2 / (7 * 0.7) == 8.000000000000002: both orders can overshoot.
    assert machines_needed(270, 100, 0.3) == 9
    assert machines_needed(39.2, 7, 0.7) == 8
    assert machines_needed(9.8, 7, 0.7) == 2
    assert machines_needed(19.6, 7, 0.7) == 4
    assert machines_needed(540, 100, 0.3) == 18
    assert machines_needed(690, 100, 0.3) == 23
    assert machines_needed(691, 100, 0.3) == 24
    # The snap must stay tiny: 0.4 of a machine in 1.5 billion is real, not float noise.
    assert machines_needed(1_500_000_000.4, 1, 1.0) == 1_500_000_001


def test_machines_errors():
    for bad in [0, -0.5, 1.01, 2]:
        with pytest.raises(ValueError):
            machines_needed(100, 10, bad)
    with pytest.raises(ValueError):
        machines_needed(100, 0, 0.5)
    with pytest.raises(ValueError):
        machines_needed(100, -10, 0.5)


# ---------- estimate ----------

def test_estimate_example():
    spec = copy.deepcopy(EXAMPLE)
    out = estimate(spec)
    assert set(out) == KEYS
    # 52 requests * 1e8 users = 5.2e9 per day, / 86,400 seconds
    assert close(out["avg_qps"], 5.2e9 / 86_400)              # 60,185.19
    assert close(out["peak_qps"], 3 * 5.2e9 / 86_400)          # 180,555.56
    assert close(out["peak_read_qps"], 3 * 5.0e9 / 86_400)     # 173,611.11
    assert close(out["peak_write_qps"], 3 * 2.0e8 / 86_400)    # 6,944.44
    # 2e8 writes/day * 1,000 B * 365 days * 5 years * 3 copies
    assert close(out["storage_bytes"], 1.095e15)
    # 173,611.11 reads/s * 20,000 B * 8 bits
    assert close(out["peak_egress_bits"], 3 * 5.0e9 / 86_400 * 20_000 * 8)   # 2.78e10
    assert out["machines"] == 151                              # 180,555.56 / 1,200 = 150.46
    assert close(out["peak_in_flight"], 3 * 5.2e9 / 86_400 * 0.05)          # 9,027.8
    assert spec == EXAMPLE, "estimate must not modify spec"


def test_estimate_round_numbers():
    # 86,400 users doing one read and one write a day: exactly 1 read/s and 1 write/s.
    spec = {
        "dau": 86_400, "reads_per_user": 1, "writes_per_user": 1,
        "read_bytes": 125, "write_bytes": 100, "peak_factor": 10,
        "replicas": 2, "years": 2, "per_machine_qps": 4, "utilization": 0.5,
        "latency_s": 0.25,
    }
    out = estimate(spec)
    assert close(out["avg_qps"], 2.0)
    assert close(out["peak_qps"], 20.0)
    assert close(out["peak_read_qps"], 10.0)
    assert close(out["peak_write_qps"], 10.0)
    assert close(out["storage_bytes"], 86_400 * 100 * 365 * 2 * 2)   # 12,614,400,000
    assert close(out["peak_egress_bits"], 10 * 125 * 8)              # 10,000 bits/s
    assert out["machines"] == 10                                     # 20 / (4 * 0.5)
    assert close(out["peak_in_flight"], 5.0)


def test_unit_traps_one_at_a_time():
    base = estimate(EXAMPLE)
    # A day is 86,400 s, not 100,000 s.
    assert not close(base["avg_qps"], 5.2e9 / 100_000, rel=1e-3)
    # A year is 365 days; years scale storage linearly.
    ten = estimate(dict(EXAMPLE, years=10))
    assert close(ten["storage_bytes"], 2 * base["storage_bytes"])
    one_copy = estimate(dict(EXAMPLE, replicas=1))
    assert close(one_copy["storage_bytes"], 3.65e14)
    # Egress is bits: 8 times the byte rate.
    assert close(base["peak_egress_bits"] / (base["peak_read_qps"] * 20_000), 8.0)
    # Writes don't add egress; reads don't add storage.
    more_writes = estimate(dict(EXAMPLE, writes_per_user=4))
    assert close(more_writes["peak_egress_bits"], base["peak_egress_bits"])
    more_reads = estimate(dict(EXAMPLE, reads_per_user=500))
    assert close(more_reads["storage_bytes"], base["storage_bytes"])
    # Slower requests: same traffic, twice the requests in flight.
    slow = estimate(dict(EXAMPLE, latency_s=0.1))
    assert close(slow["peak_qps"], base["peak_qps"])
    assert close(slow["peak_in_flight"], 2 * base["peak_in_flight"])


def test_machines_cover_reads_and_writes():
    out = estimate(dict(EXAMPLE, reads_per_user=0))
    # Only writes: 6,944.44 / 1,200 = 5.79 -> 6 machines
    assert out["machines"] == 6
    assert close(out["peak_read_qps"], 0.0)
    assert close(out["peak_egress_bits"], 0.0)


def test_machines_are_one_pool_for_all_traffic():
    # 1.5 reads/s and 0.5 writes/s on machines that do 2/s at 100%: 2 / 2 = 1 machine.
    # Rounding reads and writes up separately would say 1 + 1 = 2.
    spec = dict(EXAMPLE, dau=86_400, reads_per_user=3, writes_per_user=1, peak_factor=0.5,
                per_machine_qps=1, utilization=1.0)
    out = estimate(spec)
    assert close(out["peak_read_qps"], 1.5)
    assert close(out["peak_write_qps"], 0.5)
    assert out["machines"] == 2
    out = estimate(dict(spec, per_machine_qps=2))
    assert out["machines"] == 1


def test_huge_inputs_are_arithmetic():
    spec = dict(EXAMPLE, dau=10**15, years=10**6)
    out = estimate(spec)
    assert close(out["avg_qps"], 52 * 1e15 / 86_400)
    assert close(out["storage_bytes"], 2e15 * 1_000 * 365 * 10**6 * 3)
    assert out["machines"] == 1_504_629_630           # worked out offline with exact fractions
