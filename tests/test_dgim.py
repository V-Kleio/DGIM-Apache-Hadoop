#!/usr/bin/env python3
"""
Property tests for DGIM. Run:  python3 tests/test_dgim.py
Checks, after EVERY bit of many random streams:
  * the error bound 1/r holds for every query k
  * at most r buckets of each size, sizes are powers of 2, non-decreasing with age
  * an empty window gives exactly 0, and the bucket count is O(log N)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from dgim import DGIM, ExactWindow  # noqa: E402


def check_invariants(d):
    sizes = [s for _, s in d.buckets]                     # newest -> oldest
    assert all(s & (s - 1) == 0 for s in sizes), "size not a power of 2"
    assert sizes == sorted(sizes), "sizes must not decrease going back in time"
    for s in set(sizes):
        assert sizes.count(s) <= d.r, f"more than r buckets of size {s}"
    assert all(ts > d.t - d.N for ts, _ in d.buckets), "expired bucket kept"


def run(trials=300, seed=1):
    rng = random.Random(seed)
    worst = 0.0
    for _ in range(trials):
        N = rng.choice([1, 2, 7, 16, 64, 100, 257, 1000])
        r = rng.choice([2, 2, 3, 4])
        p = rng.random()
        bound = 1 / r
        d, e = DGIM(N, r), ExactWindow(N)
        for _ in range(rng.randint(1, 3 * N + 50)):
            b = 1 if rng.random() < p else 0
            d.add(b); e.add(b)
            check_invariants(d)
            assert len(d.buckets) <= r * (math.log2(N) + 2)
            for k in {1, max(1, N // 3), N}:
                ex, est = e.count(k), d.count(k)
                if ex == 0:
                    assert est == 0
                    continue
                err = abs(est - ex) / ex
                worst = max(worst, err)
                assert err <= bound + 1e-9, (N, r, k, ex, est)
    return worst


if __name__ == "__main__":
    w = run()
    print(f"OK - all invariants and error bounds held (worst relative error {w:.3f})")
