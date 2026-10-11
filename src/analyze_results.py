#!/usr/bin/env python3
"""
Summarise DGIM job output (one or more .tsv files from the reducer).

  python3 src/analyze_results.py results/N1000_r2.tsv
  python3 src/analyze_results.py --plot results/experiments.png results/N*_r*.tsv

For every (N, r, k) it reports mean / worst relative error per stream profile,
whether the theoretical 1/r bound held, and memory used vs. an exact counter.
"""
import argparse
import re
from collections import defaultdict
from statistics import mean

COLS = ["stream", "N", "k", "exact", "estimate", "rel_err", "worst_err",
        "buckets", "dgim_bits", "exact_bits"]


def load(path):
    m = re.search(r"_r(\d+)", path)
    r = int(m.group(1)) if m else 2
    rows = []
    with open(path) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(COLS):
                continue
            row = dict(zip(COLS, parts))
            for c in COLS[1:]:
                row[c] = float(row[c])
            row["profile"] = row["stream"].split("-")[0]
            row["r"] = r
            rows.append(row)
    return rows


def summarise(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(int(row["N"]), row["r"], int(row["k"]))].append(row)

    summary = []
    for (N, r, k), g in sorted(groups.items()):
        bound = 1 / r
        worst = max(x["worst_err"] for x in g)
        dgim_bits = mean(x["dgim_bits"] for x in g)
        print(f"\nN={N}  r={r}  k={k}   theoretical bound = {bound:.0%}")
        print(f"  {'profile':<8} {'streams':>7} {'mean err':>9} {'worst err':>10}")
        by_profile = defaultdict(list)
        for x in g:
            by_profile[x["profile"]].append(x)
        for p, xs in sorted(by_profile.items()):
            print(f"  {p:<8} {len(xs):>7} {mean(x['rel_err'] for x in xs):>9.1%} "
                  f"{max(x['worst_err'] for x in xs):>10.1%}")
        print(f"  bound held: {'YES' if worst <= bound + 1e-9 else 'NO'}  "
              f"(worst {worst:.1%})")
        print(f"  memory: {dgim_bits:.0f} bits avg (DGIM) vs {N:.0f} bits (exact) "
              f"-> {N / max(dgim_bits, 1):.1f}x smaller")
        summary.append(dict(N=N, r=r, k=k, worst=worst, bound=bound,
                            mean_err=mean(x["rel_err"] for x in g), bits=dgim_bits))
    return summary


def plot(summary, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    full = [s for s in summary if s["k"] == s["N"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    for N in sorted({s["N"] for s in full}):
        xs = sorted((s for s in full if s["N"] == N), key=lambda s: s["r"])
        rs = [s["r"] for s in xs]
        a1.plot(rs, [s["worst"] for s in xs], "o-", label=f"worst, N={N}")
        a1.plot(rs, [s["mean_err"] for s in xs], "s--", label=f"mean, N={N}")
        a2.plot(rs, [s["bits"] for s in xs], "o-", label=f"DGIM, N={N}")
    rs = sorted({s["r"] for s in full})
    a1.plot(rs, [1 / r for r in rs], "k:", label="bound 1/r")
    a1.set(xlabel="r (max buckets per size)", ylabel="relative error",
           title="Accuracy vs r")
    a2.set(xlabel="r (max buckets per size)", ylabel="bits of memory",
           title="Memory vs r", yscale="log")
    for N in sorted({s["N"] for s in full}):
        a2.axhline(N, ls=":", color="gray")
        a2.text(rs[0], N * 1.1, f"exact counter, N={N}", fontsize=8, color="gray")
    a1.legend(fontsize=8); a2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"\nchart saved -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--plot", help="save an accuracy/memory chart to this PNG")
    a = ap.parse_args()
    rows = [r for f in a.files for r in load(f)]
    s = summarise(rows)
    if a.plot:
        plot(s, a.plot)
