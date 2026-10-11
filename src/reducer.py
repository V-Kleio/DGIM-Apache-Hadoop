#!/usr/bin/env python3
"""
Hadoop Streaming REDUCER.

Receives  stream_id <TAB> timestamp <TAB> bit, grouped by stream_id and sorted
by timestamp. For each stream it runs DGIM (and, for evaluation only, an exact
sliding-window counter) and emits one line per query size k:

  stream_id  N  k  exact  estimate  rel_error  worst_rel_error  num_buckets
  dgim_bits  exact_bits

(worst_rel_error = largest error seen at the periodic checkpoints)

Settings come from environment variables (pass with -cmdenv in Hadoop):
  DGIM_WINDOW   window size N               (default 1000)
  DGIM_R        max buckets per size        (default 2)
  DGIM_QUERIES  comma list of k values, "N" means the full window
                                            (default "N,500,100")
  DGIM_EVERY    also evaluate every X bits and emit the worst error seen
                (0 = only at end of stream, default 1000)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dgim import DGIM, ExactWindow  # noqa: E402  (shipped with -file dgim.py)

N = int(os.environ.get("DGIM_WINDOW", 1000))
R = int(os.environ.get("DGIM_R", 2))
EVERY = int(os.environ.get("DGIM_EVERY", 1000))
QUERIES = []
for q in os.environ.get("DGIM_QUERIES", "N,500,100").split(","):
    q = q.strip()
    k = N if q == "N" else int(q)
    if 1 <= k <= N:
        QUERIES.append(k)


def rel_err(exact, est):
    if exact == 0:
        return 0.0 if est == 0 else 1.0
    return abs(est - exact) / exact


def flush(sid, dgim, exact, worst):
    if sid is None:
        return
    for k in QUERIES:
        e, d = exact.count(k), dgim.count(k)
        print("\t".join(map(str, [
            sid, N, k, e, f"{d:g}", f"{rel_err(e, d):.4f}",
            f"{worst[k]:.4f}", len(dgim.buckets), dgim.memory_bits(), N,
        ])))
    sys.stderr.write("reporter:counter:DGIM,StreamsProcessed,1\n")


cur, dgim, exact, worst = None, None, None, None
for line in sys.stdin:
    sid, ts, bit = line.rstrip("\n").split("\t")
    if sid != cur:
        flush(cur, dgim, exact, worst)
        cur, dgim, exact = sid, DGIM(N, R), ExactWindow(N)
        worst = {k: 0.0 for k in QUERIES}
    b = int(bit)
    dgim.add(b)
    exact.add(b)
    if EVERY and dgim.t >= N and dgim.t % EVERY == 0:
        for k in QUERIES:
            err = rel_err(exact.count(k), dgim.count(k))
            worst[k] = max(worst[k], err)
            if err > 1.0 / R + 1e-9:   # worst-case bound is 1/r (50% for r=2)
                sys.stderr.write("reporter:counter:DGIM,BoundViolations,1\n")
flush(cur, dgim, exact, worst)
