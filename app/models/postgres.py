"""
TimescaleDB-friendly SQLAlchemy models for Pipelynx time-series data.

Notes for hypertable conversion (handled by Alembic migration):
- `started_at` (PipelineRun) and `bucket_start` (MetricSnapshot) are partition columns.
- They are part of the composite primary key, which TimescaleDB requires.
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    JSON,
    Index,
    PrimaryKeyConstraint,
)
from sqlalchemy.sql import func
from app.db.base import Base


class PipelineRun(Base):
    """One row per CI/CD pipeline run — partitioned by `started_at` in TimescaleDB."""
    __tablename__ = "pipeline_runs"

    id = Column(String, nullable=False)
    organization_id = Column(String, nullable=False)
    pipeline_id = Column(String, nullable=True)
    integration_id = Column(String, nullable=False)

    # Source platform: github, gitlab, jenkins, argocd, circleci, codepipeline, bitbucket
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=True)

    # Run details
    run_number = Column(Integer, nullable=True)
    status = Column(String, nullable=False)  # success | failure | running | cancelled | queued
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Metadata
    repository = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    commit_sha = Column(String, nullable=True)
    commit_message = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    trigger = Column(String, nullable=True)

    # Errors / AI
    error_message = Column(Text, nullable=True)
    log_summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Composite PK includes the partition column — required by TimescaleDB hypertables.
        PrimaryKeyConstraint("id", "started_at", name="pk_pipeline_runs"),
        Index("ix_pipeline_runs_org_time", "organization_id", "started_at"),
        Index("ix_pipeline_runs_pipeline_time", "pipeline_id", "started_at"),
        Index("ix_pipeline_runs_status_time", "status", "started_at"),
        Index("ix_pipeline_runs_source_time", "source", "started_at"),
    )


class MetricSnapshot(Base):
    """Time-bucketed aggregate metrics — one row per (org, pipeline, bucket_size, bucket_start)."""
    __tablename__ = "metric_snapshots"

    id = Column(String, nullable=False)
    organization_id = Column(String, nullable=False)
    pipeline_id = Column(String, nullable=True)

    bucket_start = Column(DateTime(timezone=True), nullable=False)
    bucket_size = Column(String, nullable=False)  # hourly | daily | weekly

    total_runs = Column(Integer, default=0, nullable=False)
    successful_runs = Column(Integer, default=0, nullable=False)
    failed_runs = Column(Integer, default=0, nullable=False)
    cancelled_runs = Column(Integer, default=0, nullable=False)

    avg_duration_seconds = Column(Float, nullable=True)
    p50_duration_seconds = Column(Float, nullable=True)
    p95_duration_seconds = Column(Float, nullable=True)
    max_duration_seconds = Column(Float, nullable=True)

    # DORA metrics (snapshot per bucket)
    deployment_frequency = Column(Float, nullable=True)
    lead_time_seconds = Column(Float, nullable=True)
    change_failure_rate = Column(Float, nullable=True)
    mttr_seconds = Column(Float, nullable=True)

    extras = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("id", "bucket_start", name="pk_metric_snapshots"),
        Index("ix_metric_snapshots_org_bucket", "organization_id", "bucket_start"),
        Index("ix_metric_snapshots_pipeline_bucket", "pipeline_id", "bucket_start"),
        Index("ix_metric_snapshots_size_bucket", "bucket_size", "bucket_start"),
    )
