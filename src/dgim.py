#!/usr/bin/env python3
"""
DGIM (Datar-Gionis-Indyk-Motwani) algorithm.

Estimates the number of 1s in the last k bits (k <= N) of a binary stream
using O(log^2 N) bits of memory instead of the N bits an exact counter needs.

Rules kept by this implementation
  1. Every bucket ends with a 1 (we store the timestamp of that 1).
  2. Bucket sizes are powers of two (size = number of 1s inside the bucket).
  3. At most `max_per_size` buckets of each size (classic DGIM: 2).
  4. Sizes never decrease as we go back in time.
  5. A bucket is dropped once its end timestamp falls out of the window.

Estimate for the last k bits: sum of all bucket sizes inside the window,
counting only half of the oldest bucket. With max_per_size = 2 the relative
error is at most 50%.

Run this file directly for a step-by-step demo:
    python3 dgim.py 1011011000101110110010110 --window 16
"""
import math
from collections import deque
from itertools import islice


class DGIM:
    def __init__(self, window, max_per_size=2):
        if window < 1:
            raise ValueError("window must be >= 1")
        if max_per_size < 2:
            raise ValueError("max_per_size must be >= 2")
        self.N = window
        self.r = max_per_size
        self.t = 0                  # current time (number of bits seen)
        self.buckets = []           # (end_timestamp, size), newest first

    def add(self, bit):
        self.t += 1
        while self.buckets and self.buckets[-1][0] <= self.t - self.N:
            self.buckets.pop()
        if bit != 1:
            return
        self.buckets.insert(0, (self.t, 1))
        self._merge()

    def _merge(self):
        b = self.buckets
        i, size = 0, 1
        while True:
            j = i
            while j < len(b) and b[j][1] == size:
                j += 1
            if j - i <= self.r:
                return
            b[j - 2] = (b[j - 2][0], size * 2)
            del b[j - 1]
            i, size = j - 2, size * 2

    def count(self, k=None):
        """Estimated number of 1s among the last k bits (default: whole window)."""
        k = self.N if k is None else k
        if not 1 <= k <= self.N:
            raise ValueError("k must be in [1, N]")
        total = last = 0
        for ts, size in self.buckets:          # newest -> oldest
            if ts <= self.t - k:
                break
            total += size
            last = size
        if last == 0:
            return 0
        # a size-1 bucket is exact; otherwise only half of the oldest is counted
        return total - last + (1 if last == 1 else last / 2)

    def memory_bits(self):
        """Bits needed if timestamps are stored mod N and sizes as log2(size)."""
        ts_bits = max(1, math.ceil(math.log2(self.N)))
        size_bits = max(1, math.ceil(math.log2(ts_bits + 1)))
        return len(self.buckets) * (ts_bits + size_bits)

    def state(self):
        return " ".join(f"[t={ts},s={s}]" for ts, s in reversed(self.buckets))


class ExactWindow:
    """Exact sliding-window counter (N bits of memory) used only for evaluation."""

    def __init__(self, window):
        self.N = window
        self.bits = deque(maxlen=window)

    def add(self, bit):
        self.bits.append(bit)

    def count(self, k=None):
        k = self.N if k is None else k
        return sum(islice(reversed(self.bits), k))


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Step-by-step DGIM demo")
    p.add_argument("bits", help="a string of 0s and 1s, e.g. 1011011000101110")
    p.add_argument("--window", type=int, default=16)
    p.add_argument("--r", type=int, default=2, help="max buckets per size")
    a = p.parse_args()

    d, e = DGIM(a.window, a.r), ExactWindow(a.window)
    print(f"N={a.window}, max buckets per size={a.r}\n")
    print(f"{'t':>3} bit {'exact':>5} {'dgim':>5}  buckets (oldest -> newest)")
    for ch in a.bits:
        if ch not in "01":
            continue
        d.add(int(ch)); e.add(int(ch))
        print(f"{d.t:>3}  {ch}  {e.count():>5} {d.count():>5g}  {d.state()}")
