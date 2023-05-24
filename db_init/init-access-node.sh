#!/bin/sh
set -e

# https://docs.timescale.com/timescaledb/latest/how-to-guides/configuration/timescaledb-config/#timescaledb-last-tuned-string
# https://docs.timescale.com/timescaledb/latest/how-to-guides/multi-node-setup/required-configuration/

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -c "SHOW config_file"
# To achieve good query performance you need to enable partition-wise aggregation on the access node. This pushes down aggregation queries to the data nodes.
# https://www.postgresql.org/docs/12/runtime-config-query.html#enable_partitionwise_aggregate
sed -ri "s!^#?(enable_partitionwise_aggregate)\s*=.*!\1 = on!" /var/lib/postgresql/data/postgresql.conf
grep "enable_partitionwise_aggregate" /var/lib/postgresql/data/postgresql.conf
# JIT should be set to off on the access node as JIT currently doesn't work well with distributed queries.
# https://www.postgresql.org/docs/12/runtime-config-query.html#jit
sed -ri "s!^#?(jit)\s*=.*!\1 = off!" /var/lib/postgresql/data/postgresql.conf
grep "jit" /var/lib/postgresql/data/postgresql.conf

echo "Waiting for data nodes..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h timescaledb-dn-1 -U "$POSTGRES_USER" -c '\q'; do
    sleep 5s
done
until PGPASSWORD=$POSTGRES_PASSWORD psql -h timescaledb-dn-2 -U "$POSTGRES_USER" -c '\q'; do
    sleep 5s
done
until PGPASSWORD=$POSTGRES_PASSWORD psql -h timescaledb-dn-3 -U "$POSTGRES_USER" -c '\q'; do
    sleep 5s
done
until PGPASSWORD=$POSTGRES_PASSWORD psql -h timescaledb-dn-4 -U "$POSTGRES_USER" -c '\q'; do
    sleep 5s
done

echo "Connect data nodes to cluster and create distributed hypertable..."
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE logs (
    time TIMESTAMP,
    shard int,
    level TEXT,
    source TEXT,
    words TEXT[],
    logdata JSONB
);

CREATE INDEX idx_logdata ON logs USING GIN (logdata);
CREATE INDEX idx_words ON logs USING GIN (words);

SELECT add_data_node('dn1', 'timescaledb-dn-1');
SELECT add_data_node('dn2', 'timescaledb-dn-2');
SELECT add_data_node('dn3', 'timescaledb-dn-3');
SELECT add_data_node('dn4', 'timescaledb-dn-4');

SELECT create_distributed_hypertable('logs', 'time', 'shard');
SELECT set_chunk_time_interval('logs', INTERVAL '10 minutes');
ALTER TABLE logs SET (timescaledb.compress);
SELECT alter_job((SELECT add_compression_policy('logs', INTERVAL '20 minutes')), schedule_interval => INTERVAL '20 minutes');
SELECT alter_job((SELECT add_retention_policy('logs', INTERVAL '7 days')), schedule_interval => INTERVAL '1 hour');

EOSQL
