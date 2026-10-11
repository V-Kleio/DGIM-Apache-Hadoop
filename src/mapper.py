#!/usr/bin/env python3
"""
Hadoop Streaming MAPPER.

Input  (one event per line):  stream_id,timestamp,bit
Output (tab separated):       stream_id <TAB> timestamp <TAB> bit

The job is configured so that
  * the PARTITION key is field 1 (stream_id)  -> every event of a stream
    reaches the same reducer, and
  * the SORT key is field 1, then field 2 numerically -> the reducer sees each
    stream's bits in time order (secondary sort).
"""
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        sid, ts, bit = line.split(",")
        ts = int(ts)
        bit = int(bit)
    except ValueError:
        sys.stderr.write("reporter:counter:DGIM,BadRecords,1\n")
        continue
    if bit not in (0, 1):
        sys.stderr.write("reporter:counter:DGIM,BadRecords,1\n")
        continue
    print(f"{sid}\t{ts}\t{bit}")
