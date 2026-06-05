"""Metrics API endpoints"""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List

from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_org
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary")
async def get_summary(
    days: int = Query(30, ge=1, le=365),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Get high-level pipeline metrics summary"""
    return await MetricsService.organization_summary(db=db, organization_id=org["id"], days=days)


@router.get("/timeseries")
async def get_timeseries(
    days: int = Query(30, ge=1, le=365),
    bucket: str = Query("day", pattern="^(hour|day|week)$"),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> List[Dict[str, Any]]:
    """Get pipeline runs bucketed over time"""
    return await MetricsService.runs_over_time(
        db=db, organization_id=org["id"], days=days, bucket=bucket
    )


@router.get("/top-failing")
async def get_top_failing(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> List[Dict[str, Any]]:
    """Get top failing pipelines"""
    return await MetricsService.top_failing_pipelines(
        db=db, organization_id=org["id"], days=days, limit=limit
    )


@router.get("/dora")
async def get_dora(
    days: int = Query(30, ge=1, le=365),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Get DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, MTTR)"""
    return await MetricsService.dora_metrics(db=db, organization_id=org["id"], days=days)
