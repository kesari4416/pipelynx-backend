# TimescaleDB Hybrid Time-Series Store

Pipelynx uses **MongoDB for application data** (auth, integrations, alert rules)
and **TimescaleDB (PostgreSQL extension) for time-series workloads**
(`pipeline_runs` rows + aggregated `metric_snapshots`).

This module is **opt-in** — controlled by the `TIMESCALE_ENABLED` env var.
When the flag is off (the default in dev / preview), all Timescale code paths
short-circuit and the app runs MongoDB-only.

## Architecture

```
              ┌─────────────────────────┐
   Webhook ─▶ │  PipelineRunService     │
              │  .ingest_event()        │
              └──────────┬──────────────┘
                         │
              ┌──────────┴───────────┐
              ▼                      ▼
   ┌────────────────────┐  ┌────────────────────────┐
   │ MongoDB            │  │ TimescaleService       │
   │ pipeline_runs      │  │ .write_pipeline_run()  │  (no-op if flag off)
   │ (full document)    │  │ → PostgreSQL/Timescale │
   └────────────────────┘  └────────────────────────┘
```

The Mongo write is the source of truth; the Timescale write is best-effort.
A failed Timescale write is logged but does **not** fail the ingestion request.

## Enabling in production

1. **Provision PostgreSQL 14+ with the TimescaleDB extension.**
   Managed options: Timescale Cloud, AWS RDS for PostgreSQL + self-installed
   extension, Neon (Postgres-compatible), Aiven, or self-hosted.

2. **Set env vars in `backend/.env`:**
   ```
   TIMESCALE_ENABLED=true
   # Either set individual fields…
   POSTGRES_HOST=your-host
   POSTGRES_PORT=5432
   POSTGRES_USER=pipelynx
   POSTGRES_PASSWORD=...
   POSTGRES_DB=pipelynx_metrics
   # …or set DATABASE_URL (overrides the above)
   # DATABASE_URL=postgresql://user:pass@host:5432/db
   ```

3. **Restart the backend.** On startup, `init_postgres_db()` creates the base
   tables (`pipeline_runs`, `metric_snapshots`).

4. **Run the hypertable migration once:**
   ```bash
   psql "$DATABASE_URL" -f /app/backend/migrations/001_timescale_hypertables.sql
   ```
   This converts the tables into hypertables and installs retention +
   compression policies (180-day retention on raw runs, 730-day on metrics,
   compression for chunks > 30 days).

5. **Verify** via the admin endpoint:
   ```
   GET /api/v1/admin/timescale/status
   → { "enabled": true, "reachable": true, "dual_write": "active", … }
   ```

## Models

See `app/models/postgres.py`:

- `PipelineRun` — one row per CI/CD run; partition column = `started_at`
- `MetricSnapshot` — one row per `(org, pipeline, bucket_size, bucket_start)`
  tuple; partition column = `bucket_start`

Both use composite primary keys including the partition column (TimescaleDB
requirement).

## Status

- [x] Models + lazy engine + dual-write service
- [x] Ingestion path wired
- [x] Admin status endpoint
- [x] SQL migration for hypertables / policies
- [ ] Backfill script (one-shot copy from MongoDB → Timescale for existing data)
- [ ] Strawberry GraphQL API on top of Timescale (Phase 3.2)
- [ ] Materialized continuous aggregates for DORA metrics
