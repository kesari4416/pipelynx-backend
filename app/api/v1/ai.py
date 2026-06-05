"""AI-powered analysis endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_org
from app.services.ai_service import AIService
from app.services.pipeline_service import PipelineRunService

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/runs/{run_id}/analyze")
async def analyze_run(
    run_id: str,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Generate AI-powered failure analysis for a specific run (plan-gated)."""
    from app.services.entitlements import enforce_ai_quota, record_ai_usage
    await enforce_ai_quota(db, org["id"])

    run = await PipelineRunService.get_run(db, org["id"], run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    
    analysis = await AIService.summarize_run_failure(run)
    
    # Persist back to the run document
    log_summary = f"{analysis.get('root_cause', '')}\n\n{analysis.get('summary', '')}"
    if analysis.get("recommendations"):
        log_summary += "\n\nRecommendations:\n" + "\n".join(f"• {r}" for r in analysis["recommendations"])
    
    await db.pipeline_runs.update_one(
        {"id": run_id, "organization_id": org["id"]},
        {"$set": {
            "log_summary": log_summary,
            "ai_analysis": analysis,
            "ai_analyzed_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    # Increment usage counter only on success (failures don't burn quota).
    await record_ai_usage(db, org["id"])

    return {"run_id": run_id, **analysis}


@router.get("/patterns")
async def get_failure_patterns(
    days: int = Query(7, ge=1, le=90),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Analyze recent failure patterns using AI (Business+ feature)."""
    from app.services.entitlements import enforce_feature
    await enforce_feature(db, org["id"], "pattern_detection")
    return await AIService.analyze_failure_patterns(db, org["id"], days=days)


@router.get("/digest")
async def get_weekly_digest(
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Generate AI-powered weekly digest (Business+ feature)."""
    from app.services.entitlements import enforce_feature
    await enforce_feature(db, org["id"], "weekly_digest")
    return await AIService.generate_weekly_digest(db, org["id"])


@router.get("/anomalies")
async def get_anomalies(
    days: int = Query(30, ge=1, le=365),
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> List[Dict[str, Any]]:
    """Statistical anomaly detection — runs with unusual duration (Business+ feature)."""
    from app.services.entitlements import enforce_feature
    await enforce_feature(db, org["id"], "anomaly_detection")
    return await AIService.detect_anomalies(db, org["id"], days=days)
