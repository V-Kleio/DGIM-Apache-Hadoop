#!/usr/bin/env bash
# Run the DGIM MapReduce job.
# Execute INSIDE the container:
# docker exec -it dgim-hadoop bash scripts/run_job.sh
#
# Tunables (env vars):  WINDOW=1000  R=2  QUERIES="N,500,100"  REDUCERS=4
#                       STREAMS=20   LENGTH=100000   TAG=default
set -euo pipefail
cd /project

WINDOW=${WINDOW:-1000}
R=${R:-2}
QUERIES=${QUERIES:-N,500,100}
REDUCERS=${REDUCERS:-4}
STREAMS=${STREAMS:-20}
LENGTH=${LENGTH:-100000}
TAG=${TAG:-N${WINDOW}_r${R}}

IN=/dgim/input
OUT=/dgim/output/$TAG
STREAMING_JAR=$(ls $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar)

if [ ! -f data/streams.csv ]; then
    python3 src/generate_streams.py --streams "$STREAMS" --length "$LENGTH" --out data/streams.csv
fi

hdfs dfs -mkdir -p $IN
if ! hdfs dfs -test -e $IN/streams.csv; then
    hdfs dfs -put data/streams.csv $IN/
fi
hdfs dfs -rm -r -f -skipTrash $OUT

echo ">> Running DGIM job  N=$WINDOW  r=$R  queries=$QUERIES  reducers=$REDUCERS"
hadoop jar "$STREAMING_JAR" \
    -D mapreduce.job.name="DGIM N=$WINDOW r=$R" \
    -D mapreduce.job.reduces=$REDUCERS \
    -D stream.num.map.output.key.fields=2 \
    -D mapreduce.partition.keypartitioner.options=-k1,1 \
    -D mapreduce.job.output.key.comparator.class=org.apache.hadoop.mapreduce.lib.partition.KeyFieldBasedComparator \
    -D mapreduce.partition.keycomparator.options="-k1,1 -k2,2n" \
    -files src/mapper.py,src/reducer.py,src/dgim.py \
    -partitioner org.apache.hadoop.mapred.lib.KeyFieldBasedPartitioner \
    -input $IN \
    -output $OUT \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -cmdenv DGIM_WINDOW=$WINDOW \
    -cmdenv DGIM_R=$R \
    -cmdenv DGIM_QUERIES=$QUERIES

mkdir -p results
hdfs dfs -getmerge $OUT results/$TAG.tsv
echo ">> Results: results/$TAG.tsv  ($(wc -l <results/$TAG.tsv) lines)"
python3 src/analyze_results.py results/$TAG.tsv
