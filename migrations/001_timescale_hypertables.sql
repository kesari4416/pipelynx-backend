-- ============================================================================
-- Pipelynx — TimescaleDB hypertable migration
-- ============================================================================
-- Run this once after `init_postgres_db()` has created the base tables
-- (i.e., after starting the backend with TIMESCALE_ENABLED=true at least once).
--
-- Prerequisites:
--   - PostgreSQL 14+ with the TimescaleDB extension installed
--   - The Pipelynx app user has CREATE on the database
--
-- This migration:
--   1. Enables the timescaledb extension
--   2. Converts `pipeline_runs` and `metric_snapshots` to hypertables
--   3. Adds retention + compression policies (Business / Enterprise plan defaults)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ---- pipeline_runs hypertable ----------------------------------------------
SELECT create_hypertable(
    'pipeline_runs',
    'started_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists       => TRUE
);

-- Compress chunks older than 30 days (CI/CD log data compresses ~10x)
ALTER TABLE pipeline_runs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, source',
    timescaledb.compress_orderby   = 'started_at DESC'
);
SELECT add_compression_policy('pipeline_runs', INTERVAL '30 days', if_not_exists => TRUE);

-- Default retention: 180 days (Business plan). Enterprise tier can drop / extend.
SELECT add_retention_policy('pipeline_runs', INTERVAL '180 days', if_not_exists => TRUE);


-- ---- metric_snapshots hypertable -------------------------------------------
SELECT create_hypertable(
    'metric_snapshots',
    'bucket_start',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists       => TRUE
);

ALTER TABLE metric_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, bucket_size',
    timescaledb.compress_orderby   = 'bucket_start DESC'
);
SELECT add_compression_policy('metric_snapshots', INTERVAL '90 days', if_not_exists => TRUE);

-- Aggregated metrics retained for 2 years for trend analysis
SELECT add_retention_policy('metric_snapshots', INTERVAL '730 days', if_not_exists => TRUE);
