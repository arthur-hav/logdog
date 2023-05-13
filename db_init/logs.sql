CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE event (
    time TIMESTAMP,
    id SERIAL,
    key TEXT,
    value TEXT,
    metric DOUBLE PRECISION
    );

SELECT create_hypertable('event', 'time');
SELECT set_chunk_time_interval('event', INTERVAL '10 minutes');
ALTER TABLE event SET (timescaledb.compress);
SELECT alter_job((SELECT add_compression_policy('event', INTERVAL '70 minutes')), schedule_interval => INTERVAL '70 minutes');
SELECT alter_job((SELECT add_retention_policy('event', INTERVAL '300 minutes')), schedule_interval => INTERVAL '300 minutes');
