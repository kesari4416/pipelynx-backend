"""
Pipeline Run Service - handles ingestion, storage, and querying of pipeline runs.
"""
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import logging

from app.models.mongodb import PipelineRun
from app.services.event_parsers.registry import parse_event

logger = logging.getLogger(__name__)


def _serialize_datetimes(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime fields to ISO strings for MongoDB storage"""
    for key in ("started_at", "completed_at", "created_at", "updated_at"):
        if doc.get(key) and isinstance(doc[key], datetime):
            doc[key] = doc[key].isoformat()
    return doc


def _deserialize_datetimes(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ISO string datetime fields back to datetime objects"""
    for key in ("started_at", "completed_at", "created_at", "updated_at"):
        if doc.get(key) and isinstance(doc[key], str):
            try:
                doc[key] = datetime.fromisoformat(doc[key])
            except ValueError:
                pass
    return doc


class PipelineRunService:
    """Service for managing pipeline runs"""
    
    @staticmethod
    async def _find_integration(db: AsyncIOMotorDatabase, source: str) -> Optional[Dict[str, Any]]:
        """Helper: find first active integration for a CI/CD source"""
        return await db.integrations.find_one(
            {"type": source, "is_active": True},
            {"_id": 0}
        )
    
    @staticmethod
    async def _find_matching_pipeline(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        integration_id: str,
        repository: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Helper: find existing pipeline record matching repo + integration"""
        if not repository:
            return None
        return await db.pipelines.find_one(
            {
                "organization_id": organization_id,
                "integration_id": integration_id,
                "repository": repository,
            },
            {"_id": 0}
        )
    
    @staticmethod
    async def _persist_run(
        db: AsyncIOMotorDatabase,
        run: PipelineRun,
        source: str,
    ) -> None:
        """Helper: upsert pipeline run by (org_id, source, external_id)"""
        existing = await db.pipeline_runs.find_one(
            {
                "organization_id": run.organization_id,
                "source": source,
                "external_id": run.external_id,
            },
            {"_id": 0}
        )
        
        run_doc = run.model_dump()
        run_doc = _serialize_datetimes(run_doc)
        
        if existing:
            run_doc["id"] = existing["id"]
            run_doc["created_at"] = existing.get("created_at", run_doc["created_at"])
            run_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.pipeline_runs.update_one({"id": existing["id"]}, {"$set": run_doc})
            logger.info(f"Updated pipeline run {existing['id']} from {source}")
        else:
            await db.pipeline_runs.insert_one(run_doc)
            logger.info(f"Created pipeline run {run.id} from {source}")
    
    @classmethod
    async def ingest_event(
        cls,
        db: AsyncIOMotorDatabase,
        source: str,
        event_type: Optional[str],
        payload: Dict[str, Any],
    ) -> Optional[PipelineRun]:
        """
        Ingest a CI/CD event, parse it, and store/update the pipeline run.
        Refactored to delegate to helper methods.
        """
        # 1. Parse event
        normalized = parse_event(source, event_type, payload)
        if not normalized:
            logger.info(f"Event from {source} (type={event_type}) ignored")
            return None
        
        # 2. Match to integration
        integration = await cls._find_integration(db, source)
        if not integration:
            logger.warning(f"No active integration found for source: {source}")
            return None
        
        organization_id = integration["organization_id"]
        integration_id = integration["id"]
        
        # 3. Match to pipeline (optional)
        pipeline = await cls._find_matching_pipeline(
            db, organization_id, integration_id, normalized.get("repository")
        )
        
        # 4. Build PipelineRun
        run_data = {
            "organization_id": organization_id,
            "integration_id": integration_id,
            "pipeline_id": pipeline["id"] if pipeline else None,
            "raw_payload": payload,
            **normalized,
        }
        run = PipelineRun(**run_data)
        
        # 5. Persist (upsert)
        await cls._persist_run(db, run, source)

        # 5b. Dual-write to TimescaleDB (no-op when feature flag is off)
        try:
            from app.services.timescale_service import TimescaleService
            run_dict_ts = run.model_dump()
            run_dict_ts["source"] = source
            await TimescaleService.write_pipeline_run(run_dict_ts)
        except Exception as ts_err:
            logger.warning(f"Timescale dual-write skipped: {ts_err}")
        
        # 6. Auto-create pipeline if needed
        if not pipeline and normalized.get("repository"):
            await cls._auto_create_pipeline(db, organization_id, integration_id, normalized)
        
        # 7. Evaluate alert rules against this run (fire-and-forget)
        try:
            from app.services.notification_service import AlertEngine
            run_dict = run.model_dump()
            # Convert datetime fields to strings for alert engine
            for k in ("started_at", "completed_at", "created_at", "updated_at"):
                if run_dict.get(k) and isinstance(run_dict[k], datetime):
                    run_dict[k] = run_dict[k].isoformat()
            await AlertEngine.evaluate(db, run_dict, organization_id)
        except Exception as alert_err:
            logger.error(f"Alert evaluation failed: {alert_err}", exc_info=True)
        
        return run
    
    @staticmethod
    async def _auto_create_pipeline(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        integration_id: str,
        normalized: Dict[str, Any],
    ) -> None:
        """Auto-create pipeline record from incoming event"""
        from app.models.mongodb import Pipeline
        
        pipeline = Pipeline(
            organization_id=organization_id,
            integration_id=integration_id,
            name=normalized.get("name") or normalized.get("repository", "unknown"),
            repository=normalized.get("repository", ""),
            branch=normalized.get("branch"),
            external_id=normalized.get("external_id", ""),
        )
        doc = pipeline.model_dump()
        doc["created_at"] = doc["created_at"].isoformat()
        doc["updated_at"] = doc["updated_at"].isoformat()
        await db.pipelines.insert_one(doc)
        logger.info(f"Auto-created pipeline {pipeline.id} for repo {normalized.get('repository')}")
    
    @staticmethod
    async def list_runs(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        pipeline_id: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """List pipeline runs with optional filters"""
        query: Dict[str, Any] = {"organization_id": organization_id}
        if pipeline_id:
            query["pipeline_id"] = pipeline_id
        if source:
            query["source"] = source
        if status:
            query["status"] = status
        
        cursor = db.pipeline_runs.find(query, {"_id": 0, "raw_payload": 0}).sort("created_at", -1).skip(skip).limit(limit)
        runs = await cursor.to_list(limit)
        return [_deserialize_datetimes(r) for r in runs]
    
    @staticmethod
    async def get_run(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        run_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a single pipeline run by ID"""
        run = await db.pipeline_runs.find_one(
            {"id": run_id, "organization_id": organization_id},
            {"_id": 0}
        )
        return _deserialize_datetimes(run) if run else None
    
    @staticmethod
    async def count_runs(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        pipeline_id: Optional[str] = None,
    ) -> int:
        """Count total runs for org/pipeline"""
        query: Dict[str, Any] = {"organization_id": organization_id}
        if pipeline_id:
            query["pipeline_id"] = pipeline_id
        return await db.pipeline_runs.count_documents(query)
