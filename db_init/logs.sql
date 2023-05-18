CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE logs (
    time TIMESTAMP,
    logdata JSONB
);

CREATE INDEX idx_logdata ON logs USING GIN (logdata);

SELECT create_hypertable('logs', 'time');
SELECT set_chunk_time_interval('logs', INTERVAL '10 minutes');
ALTER TABLE logs SET (timescaledb.compress);
SELECT alter_job((SELECT add_compression_policy('logs', INTERVAL '20 minutes')), schedule_interval => INTERVAL '20 minutes');
SELECT alter_job((SELECT add_retention_policy('logs', INTERVAL '7 days')), schedule_interval => INTERVAL '7 days');


/*
CREATE TABLE metrics (
    time TIMESTAMP,
    tags TEXT[],
    metric NUMERIC
);

CREATE INDEX idx_tag ON metrics USING GIN (tags);

SELECT create_hypertable('metrics', 'time');
SELECT set_chunk_time_interval('metrics', INTERVAL '10 minutes');
ALTER TABLE metrics SET (timescaledb.compress);
SELECT alter_job((SELECT add_compression_policy('metrics', INTERVAL '20 minutes')), schedule_interval => INTERVAL '20 minutes');
SELECT alter_job((SELECT add_retention_policy('metrics', INTERVAL '7 days')), schedule_interval => INTERVAL '7 days');
*/

CREATE TABLE filters (
    id BIGSERIAL PRIMARY KEY,
    list_filters JSONB
);