# Single-node (pseudo-distributed) Apache Hadoop: HDFS + YARN + MapReduce,
# plus Python 3 for Hadoop Streaming.  Works on x86_64 and ARM (Apple Silicon).
FROM ubuntu:22.04

ARG HADOOP_VERSION=3.3.6
ARG HADOOP_URL=https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jdk-headless python3 python3-pip curl ca-certificates procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir matplotlib \
    # architecture-independent JAVA_HOME
    && ln -sfn "$(dirname "$(dirname "$(readlink -f "$(which javac)")")")" /opt/java

RUN curl -fSL "$HADOOP_URL" -o /tmp/hadoop.tgz \
    && tar -xzf /tmp/hadoop.tgz -C /opt \
    && mv /opt/hadoop-${HADOOP_VERSION} /opt/hadoop \
    && rm /tmp/hadoop.tgz /opt/hadoop/share/doc -rf

ENV JAVA_HOME=/opt/java \
    HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH \
    # Hadoop 3 refuses to start daemons as root unless these are set
    HDFS_NAMENODE_USER=root HDFS_DATANODE_USER=root HDFS_SECONDARYNAMENODE_USER=root \
    YARN_RESOURCEMANAGER_USER=root YARN_NODEMANAGER_USER=root MAPRED_HISTORYSERVER_USER=root

COPY conf/*.xml $HADOOP_CONF_DIR/
COPY entrypoint.sh /entrypoint.sh
RUN echo "export JAVA_HOME=/opt/java" >> $HADOOP_CONF_DIR/hadoop-env.sh \
    && chmod +x /entrypoint.sh

# 9870 = HDFS NameNode UI, 8088 = YARN ResourceManager UI, 19888 = JobHistory UI
EXPOSE 9870 8088 19888
WORKDIR /project
ENTRYPOINT ["/entrypoint.sh"]
