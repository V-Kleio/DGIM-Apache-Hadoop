#!/usr/bin/env bash
# Run the job for several window sizes and r values, then chart the trade-off
# between memory and accuracy.
# Execute INSIDE the container:
# docker exec -it dgim-hadoop bash scripts/run_experiments.sh
set -euo pipefail
cd /project

for N in 1000 10000; do
    for R in 2 3 4; do
        WINDOW=$N R=$R QUERIES="N" bash scripts/run_job.sh
    done
done

python3 src/analyze_results.py --plot results/experiments.png results/N*_r*.tsv
