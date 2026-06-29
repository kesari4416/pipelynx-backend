"""Pipeline Runs API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any

from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_org
from app.services.pipeline_service import PipelineRunService

router = APIRouter(prefix="/runs", tags=["Pipeline Runs"])


@router.get("/live")
async def list_live_runs(
    limit: int = Query(100, ge=1, le=500),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """
    Return in-flight pipeline runs across all integrations.

    'In-flight' = status in {running, queued}, plus the most recent few completed runs per source
    so the live view always has something to show even when nothing is mid-build.
    """
    in_flight = await db.pipeline_runs.find(
        {
            "organization_id": org["id"],
            "status": {"$in": ["running", "queued"]},
        },
        {"_id": 0, "raw_payload": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)

    # Recent completed runs (last 20 of any status) for the right-hand timeline
    recent = await db.pipeline_runs.find(
        {"organization_id": org["id"]},
        {"_id": 0, "raw_payload": 0},
    ).sort("created_at", -1).limit(20).to_list(20)

    # Per-source counts (active integrations)
    sources_agg = await db.pipeline_runs.aggregate([
        {"$match": {"organization_id": org["id"]}},
        {"$group": {
            "_id": "$source",
            "total": {"$sum": 1},
            "running": {"$sum": {"$cond": [{"$eq": ["$status", "running"]}, 1, 0]}},
            "queued": {"$sum": {"$cond": [{"$eq": ["$status", "queued"]}, 1, 0]}},
            "failure": {"$sum": {"$cond": [{"$eq": ["$status", "failure"]}, 1, 0]}},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
        }},
    ]).to_list(50)

    return {
        "in_flight": in_flight,
        "recent": recent,
        "sources": [
            {
                "source": s["_id"],
                "total": s.get("total", 0),
                "running": s.get("running", 0),
                "queued": s.get("queued", 0),
                "failure": s.get("failure", 0),
                "success": s.get("success", 0),
            }
            for s in sources_agg if s.get("_id")
        ],
        "as_of": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


@router.get("/")
async def list_runs(
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID"),
    source: Optional[str] = Query(None, description="Filter by CI/CD source (github, gitlab, etc.)"),
    run_status: Optional[str] = Query(None, alias="status", description="Filter by run status"),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """List pipeline runs with optional filters"""
    runs = await PipelineRunService.list_runs(
        db=db,
        organization_id=org["id"],
        pipeline_id=pipeline_id,
        source=source,
        status=run_status,
        limit=limit,
        skip=skip,
    )
    total = await PipelineRunService.count_runs(db=db, organization_id=org["id"], pipeline_id=pipeline_id)
    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "runs": runs,
    }


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Get pipeline run details by ID"""
    run = await PipelineRunService.get_run(db=db, organization_id=org["id"], run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run
