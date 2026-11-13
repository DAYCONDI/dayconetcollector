-- DaycoNet schema. Run as postgres after create_db.sql:
--   psql -U postgres -d dayconet -f db\schema.sql
-- Idempotent: safe to run more than once.

CREATE TABLE IF NOT EXISTS traffic_raw (
    id           BIGSERIAL PRIMARY KEY,
    captured_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    pid          INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    exe_path     TEXT,
    bytes_sent   BIGINT NOT NULL,
    bytes_recv   BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_traffic_raw_time
    ON traffic_raw (captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_raw_proc_time
    ON traffic_raw (process_name, captured_at DESC);

CREATE TABLE IF NOT EXISTS traffic_hourly (
    bucket_start TIMESTAMPTZ NOT NULL,
    process_name TEXT NOT NULL,
    bytes_sent   BIGINT NOT NULL DEFAULT 0,
    bytes_recv   BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket_start, process_name)
);

CREATE INDEX IF NOT EXISTS idx_traffic_hourly_time
    ON traffic_hourly (bucket_start DESC);

-- Grants. Writer needs DELETE for pruning old rows; UPDATE for ON CONFLICT DO UPDATE.
GRANT SELECT, INSERT, UPDATE, DELETE ON traffic_raw, traffic_hourly TO dayconet_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dayconet_writer;
GRANT SELECT ON traffic_raw, traffic_hourly TO dayconet_reader;
