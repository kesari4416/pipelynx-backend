"""Pipeline Runs API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any

from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_org
from app.services.pipeline_service import PipelineRunService

router = APIRouter(prefix="/runs", tags=["Pipeline Runs"])


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
