-- Traffic collection schema for the Dayconet collector.
-- Idempotent: every CREATE uses IF NOT EXISTS. No grants, users, or DROPs.

-- Raw per-packet/process traffic samples.
CREATE TABLE IF NOT EXISTS traffic_raw (
    id           BIGSERIAL PRIMARY KEY,
    captured_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    pid          INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    exe_path     TEXT,
    bytes_sent   BIGINT NOT NULL,
    bytes_recv   BIGINT NOT NULL
);

-- Hourly aggregated traffic per process.
CREATE TABLE IF NOT EXISTS traffic_hourly (
    bucket_start TIMESTAMPTZ NOT NULL,
    process_name TEXT NOT NULL,
    bytes_sent   BIGINT NOT NULL DEFAULT 0,
    bytes_recv   BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket_start, process_name)
);

-- Indexes.
CREATE INDEX IF NOT EXISTS idx_traffic_raw_time ON traffic_raw (captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_raw_proc_time ON traffic_raw (process_name, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_hourly_time ON traffic_hourly (bucket_start DESC);
