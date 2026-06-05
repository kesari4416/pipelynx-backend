"""
Metrics Service - calculates DORA and pipeline performance metrics.
"""
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for computing pipeline metrics including DORA metrics"""
    
    @staticmethod
    async def organization_summary(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get high-level metrics summary for an organization"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Use aggregation pipeline for efficient counting
        pipeline = [
            {"$match": {
                "organization_id": organization_id,
                "created_at": {"$gte": since},
            }},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_seconds"},
            }}
        ]
        
        results = await db.pipeline_runs.aggregate(pipeline).to_list(100)
        
        total = sum(r["count"] for r in results)
        by_status = {r["_id"]: r["count"] for r in results}
        success_count = by_status.get("success", 0)
        failure_count = by_status.get("failure", 0)
        
        completed = success_count + failure_count
        success_rate = (success_count / completed * 100) if completed > 0 else 0
        failure_rate = (failure_count / completed * 100) if completed > 0 else 0
        
        # Average duration across all successful runs
        success_records = [r for r in results if r["_id"] == "success"]
        avg_duration = success_records[0]["avg_duration"] if success_records and success_records[0]["avg_duration"] else 0
        
        # Deployment frequency: successful runs / days
        deployment_frequency = success_count / max(days, 1)
        
        return {
            "period_days": days,
            "total_runs": total,
            "successful_runs": success_count,
            "failed_runs": failure_count,
            "running_runs": by_status.get("running", 0),
            "queued_runs": by_status.get("queued", 0),
            "cancelled_runs": by_status.get("cancelled", 0),
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "avg_duration_seconds": round(avg_duration, 2) if avg_duration else 0,
            "deployment_frequency_per_day": round(deployment_frequency, 2),
            "by_status": by_status,
        }
    
    @staticmethod
    async def runs_over_time(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 30,
        bucket: str = "day",  # "hour", "day", "week"
    ) -> List[Dict[str, Any]]:
        """Get pipeline run counts bucketed by time"""
        since = (datetime.now(timezone.utc) - timedelta(days=days))
        since_iso = since.isoformat()
        
        # Determine date format for grouping
        if bucket == "hour":
            date_format = "%Y-%m-%dT%H:00:00"
        elif bucket == "week":
            date_format = "%Y-W%U"
        else:  # day
            date_format = "%Y-%m-%d"
        
        pipeline = [
            {"$match": {
                "organization_id": organization_id,
                "created_at": {"$gte": since_iso},
            }},
            {"$addFields": {
                # Parse ISO string into a date for grouping
                "parsed_date": {"$dateFromString": {"dateString": "$created_at", "onError": None}}
            }},
            {"$match": {"parsed_date": {"$ne": None}}},
            {"$group": {
                "_id": {
                    "bucket": {"$dateToString": {"format": date_format, "date": "$parsed_date"}},
                    "status": "$status",
                },
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.bucket": 1}},
        ]
        
        results = await db.pipeline_runs.aggregate(pipeline).to_list(1000)
        
        # Reshape into time-series format
        buckets: Dict[str, Dict[str, int]] = {}
        for r in results:
            bucket_key = r["_id"]["bucket"]
            status = r["_id"]["status"]
            if bucket_key not in buckets:
                buckets[bucket_key] = {
                    "bucket": bucket_key,
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "running": 0,
                    "cancelled": 0,
                    "queued": 0,
                    "skipped": 0,
                }
            buckets[bucket_key]["total"] += r["count"]
            if status in buckets[bucket_key]:
                buckets[bucket_key][status] = r["count"]
        
        return sorted(buckets.values(), key=lambda x: x["bucket"])
    
    @staticmethod
    async def top_failing_pipelines(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get pipelines with the most failures"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        pipeline = [
            {"$match": {
                "organization_id": organization_id,
                "status": "failure",
                "created_at": {"$gte": since},
            }},
            {"$group": {
                "_id": {
                    "pipeline_id": "$pipeline_id",
                    "name": "$name",
                    "repository": "$repository",
                    "source": "$source",
                },
                "failure_count": {"$sum": 1},
                "last_failure": {"$max": "$created_at"},
            }},
            {"$sort": {"failure_count": -1}},
            {"$limit": limit},
        ]
        
        results = await db.pipeline_runs.aggregate(pipeline).to_list(limit)
        return [
            {
                "pipeline_id": r["_id"].get("pipeline_id"),
                "name": r["_id"].get("name"),
                "repository": r["_id"].get("repository"),
                "source": r["_id"].get("source"),
                "failure_count": r["failure_count"],
                "last_failure": r["last_failure"],
            }
            for r in results
        ]
    
    @staticmethod
    def _parse_run_timestamp(run: Dict[str, Any]) -> Optional[datetime]:
        """Helper: parse 'created_at' from a run record into datetime"""
        created_at = run.get("created_at")
        if not created_at:
            return None
        if isinstance(created_at, datetime):
            return created_at
        try:
            return datetime.fromisoformat(created_at)
        except ValueError:
            return None
    
    @staticmethod
    def _compute_lead_time(successes: List[Dict[str, Any]]) -> float:
        """Helper: compute average lead time (proxy: avg duration of successful runs)"""
        durations = [r.get("duration_seconds") for r in successes if r.get("duration_seconds")]
        return sum(durations) / len(durations) if durations else 0
    
    @staticmethod
    def _group_runs_by_pipeline(runs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Helper: group runs by pipeline identifier"""
        by_pipeline: Dict[str, List[Dict[str, Any]]] = {}
        for r in runs:
            key = r.get("pipeline_id") or r.get("name")
            if key:
                by_pipeline.setdefault(key, []).append(r)
        return by_pipeline
    
    @classmethod
    def _compute_recovery_times(cls, runs: List[Dict[str, Any]]) -> List[float]:
        """Helper: compute recovery times (seconds between failure → next success per pipeline)"""
        recovery_times: List[float] = []
        for pipeline_runs in cls._group_runs_by_pipeline(runs).values():
            last_failure_time: Optional[datetime] = None
            for r in pipeline_runs:
                t = cls._parse_run_timestamp(r)
                if not t:
                    continue
                if r["status"] == "failure":
                    last_failure_time = t
                elif r["status"] == "success" and last_failure_time:
                    recovery_times.append((t - last_failure_time).total_seconds())
                    last_failure_time = None
        return recovery_times
    
    @classmethod
    async def dora_metrics(
        cls,
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Calculate DORA metrics. Now delegates to focused helper methods.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        runs = await db.pipeline_runs.find(
            {
                "organization_id": organization_id,
                "created_at": {"$gte": since},
                "status": {"$in": ["success", "failure"]},
            },
            {"_id": 0, "raw_payload": 0}
        ).sort("created_at", 1).to_list(10000)
        
        total = len(runs)
        successes = [r for r in runs if r["status"] == "success"]
        failures = [r for r in runs if r["status"] == "failure"]
        
        deployment_frequency = len(successes) / max(days, 1)
        change_failure_rate = (len(failures) / total * 100) if total > 0 else 0
        avg_lead_time = cls._compute_lead_time(successes)
        recovery_times = cls._compute_recovery_times(runs)
        mttr_seconds = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        
        return {
            "period_days": days,
            "deployment_frequency_per_day": round(deployment_frequency, 2),
            "lead_time_seconds": round(avg_lead_time, 2),
            "change_failure_rate_percent": round(change_failure_rate, 2),
            "mttr_seconds": round(mttr_seconds, 2),
            "total_deployments": len(successes),
            "total_failures": len(failures),
            "recoveries_observed": len(recovery_times),
        }
