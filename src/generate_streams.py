#!/usr/bin/env python3
"""
Generate synthetic binary streams for the DGIM experiment.

Output: one event per line, CSV  ->  stream_id,timestamp,bit
Lines are written in SHUFFLED order on purpose, so the MapReduce job has to
rebuild the time order itself (shuffle + secondary sort) before DGIM runs.

Stream profiles (to show DGIM behaves the same regardless of density):
  sparse  - P(1) = 0.05
  medium  - P(1) = 0.5
  dense   - P(1) = 0.95
  bursty  - alternates long runs of mostly-1s and mostly-0s
  sensor  - periodic signal (1 when a sine wave is above a threshold) + noise

Usage:
  python3 generate_streams.py --streams 20 --length 100000 --out data/streams.csv
"""
import argparse
import math
import os
import random

PROFILES = ["sparse", "medium", "dense", "bursty", "sensor"]


def bits_for(profile, length, rng):
    if profile == "sparse":
        return [1 if rng.random() < 0.05 else 0 for _ in range(length)]
    if profile == "medium":
        return [1 if rng.random() < 0.5 else 0 for _ in range(length)]
    if profile == "dense":
        return [1 if rng.random() < 0.95 else 0 for _ in range(length)]
    if profile == "bursty":
        out, on = [], False
        while len(out) < length:
            run = rng.randint(200, 3000)
            p = 0.9 if on else 0.05
            out.extend(1 if rng.random() < p else 0 for _ in range(run))
            on = not on
        return out[:length]
    if profile == "sensor":
        period = rng.randint(500, 5000)
        return [
            1 if math.sin(2 * math.pi * t / period) + rng.gauss(0, 0.3) > 0.3 else 0
            for t in range(length)
        ]
    raise ValueError(profile)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--streams", type=int, default=20)
    p.add_argument("--length", type=int, default=100_000, help="bits per stream")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="data/streams.csv")
    a = p.parse_args()

    rng = random.Random(a.seed)
    rows = []
    for s in range(a.streams):
        profile = PROFILES[s % len(PROFILES)]
        sid = f"{profile}-{s:03d}"
        for t, b in enumerate(bits_for(profile, a.length, rng), start=1):
            rows.append(f"{sid},{t},{b}\n")
    rng.shuffle(rows)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        f.writelines(rows)
    print(f"wrote {len(rows):,} events ({a.streams} streams x {a.length:,} bits) -> {a.out}")


if __name__ == "__main__":
    main()
