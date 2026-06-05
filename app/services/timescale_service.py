"""
TimescaleDB dual-write service.

This service is a thin, fault-tolerant adapter. It is intentionally a no-op when
`settings.TIMESCALE_ENABLED` is false so the rest of the application can be
written against a single interface, regardless of whether Timescale is provisioned.

Errors are logged and swallowed: a failed time-series write must never break
the primary MongoDB ingestion path.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select, delete

from app.core.config import settings
from app.db.postgres import get_engine

logger = logging.getLogger(__name__)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


class TimescaleService:
    """All methods are coroutines and are no-ops when Timescale is disabled."""

    @staticmethod
    def is_enabled() -> bool:
        return settings.TIMESCALE_ENABLED

    @classmethod
    async def write_pipeline_run(cls, run_doc: Dict[str, Any]) -> None:
        """
        Upsert a pipeline run row into the `pipeline_runs` hypertable.
        Accepts the same flat dict shape used by the Mongo path.
        """
        if not cls.is_enabled():
            return

        try:
            from app.models.postgres import PipelineRun  # local import to avoid SQLA init when disabled

            engine = get_engine()
            if engine is None:
                return

            started_at = _parse_dt(run_doc.get("started_at")) or datetime.now(timezone.utc)
            row_values = {
                "id": run_doc.get("id") or str(uuid.uuid4()),
                "organization_id": run_doc["organization_id"],
                "pipeline_id": run_doc.get("pipeline_id"),
                "integration_id": run_doc["integration_id"],
                "source": run_doc.get("source") or run_doc.get("platform") or "unknown",
                "external_id": run_doc.get("external_id"),
                "run_number": run_doc.get("run_number"),
                "status": run_doc.get("status") or "unknown",
                "started_at": started_at,
                "completed_at": _parse_dt(run_doc.get("completed_at")),
                "duration_seconds": run_doc.get("duration_seconds"),
                "repository": run_doc.get("repository"),
                "branch": run_doc.get("branch"),
                "commit_sha": run_doc.get("commit_sha"),
                "commit_message": run_doc.get("commit_message"),
                "author": run_doc.get("author"),
                "trigger": run_doc.get("trigger"),
                "error_message": run_doc.get("error_message"),
                "log_summary": run_doc.get("log_summary"),
            }

            # Use SQLAlchemy 2.x async session directly via engine.begin()
            from sqlalchemy.ext.asyncio import AsyncSession
            async with AsyncSession(engine, expire_on_commit=False) as session:
                # Delete existing (id, started_at) tuple then insert — simplest, hypertable-safe upsert.
                await session.execute(
                    delete(PipelineRun).where(
                        PipelineRun.id == row_values["id"],
                        PipelineRun.started_at == started_at,
                    )
                )
                session.add(PipelineRun(**row_values))
                await session.commit()
            logger.debug("Timescale: wrote pipeline_run id=%s", row_values["id"])
        except Exception as exc:  # noqa: BLE001 — non-fatal
            logger.warning("Timescale dual-write (run) failed: %s", exc)

    @classmethod
    async def write_metric_snapshot(cls, snapshot: Dict[str, Any]) -> None:
        """Insert a metric snapshot row. `bucket_start` and `bucket_size` are required."""
        if not cls.is_enabled():
            return

        try:
            from app.models.postgres import MetricSnapshot

            engine = get_engine()
            if engine is None:
                return

            bucket_start = _parse_dt(snapshot.get("bucket_start")) or datetime.now(timezone.utc)
            row_values = {
                "id": snapshot.get("id") or str(uuid.uuid4()),
                "organization_id": snapshot["organization_id"],
                "pipeline_id": snapshot.get("pipeline_id"),
                "bucket_start": bucket_start,
                "bucket_size": snapshot.get("bucket_size", "daily"),
                "total_runs": snapshot.get("total_runs", 0),
                "successful_runs": snapshot.get("successful_runs", 0),
                "failed_runs": snapshot.get("failed_runs", 0),
                "cancelled_runs": snapshot.get("cancelled_runs", 0),
                "avg_duration_seconds": snapshot.get("avg_duration_seconds"),
                "p50_duration_seconds": snapshot.get("p50_duration_seconds"),
                "p95_duration_seconds": snapshot.get("p95_duration_seconds"),
                "max_duration_seconds": snapshot.get("max_duration_seconds"),
                "deployment_frequency": snapshot.get("deployment_frequency"),
                "lead_time_seconds": snapshot.get("lead_time_seconds"),
                "change_failure_rate": snapshot.get("change_failure_rate"),
                "mttr_seconds": snapshot.get("mttr_seconds"),
                "extras": snapshot.get("extras"),
            }
            from sqlalchemy.ext.asyncio import AsyncSession
            async with AsyncSession(engine, expire_on_commit=False) as session:
                session.add(MetricSnapshot(**row_values))
                await session.commit()
            logger.debug("Timescale: wrote metric_snapshot id=%s", row_values["id"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Timescale dual-write (snapshot) failed: %s", exc)

    @classmethod
    async def count_runs(cls, organization_id: str) -> Optional[int]:
        """Quick sanity query used by the admin status endpoint."""
        if not cls.is_enabled():
            return None
        try:
            from app.models.postgres import PipelineRun
            from sqlalchemy.ext.asyncio import AsyncSession
            engine = get_engine()
            if engine is None:
                return None
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(PipelineRun).where(PipelineRun.organization_id == organization_id)
                )
                return len(result.all())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Timescale count failed: %s", exc)
            return None
