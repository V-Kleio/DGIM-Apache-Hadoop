#!/usr/bin/env bash
set -e

if [ ! -d /hadoop-data/namenode/current ]; then
    echo ">> First start: formatting HDFS NameNode"
    hdfs namenode -format -force -nonInteractive
fi

echo ">> Starting HDFS"
hdfs --daemon start namenode
hdfs --daemon start datanode

echo ">> Starting YARN"
yarn --daemon start resourcemanager
yarn --daemon start nodemanager

echo ">> Starting MapReduce JobHistory server"
mapred --daemon start historyserver

echo ">> Waiting for HDFS to leave safe mode"
hdfs dfsadmin -safemode wait

echo ">> Hadoop is up:"
echo "   NameNode UI        http://localhost:9870"
echo "   ResourceManager UI http://localhost:8088"
echo "   JobHistory UI      http://localhost:19888"
jps

tail -F $HADOOP_HOME/logs/*.log
