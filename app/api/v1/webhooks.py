"""
Webhook endpoints for all 7 CI/CD platforms.
Events are parsed, normalized, and stored as PipelineRun records.
"""
from fastapi import APIRouter, Depends, Request, Header, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any
import logging

from app.db.mongodb import get_mongodb
from app.services.pipeline_service import PipelineRunService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def _process_webhook(
    db: AsyncIOMotorDatabase,
    source: str,
    event_type: Optional[str],
    payload: Dict[str, Any],
) -> None:
    """Background task: process webhook event"""
    try:
        await PipelineRunService.ingest_event(db, source, event_type, payload)
    except Exception as e:
        logger.error(f"Error processing {source} webhook: {e}", exc_info=True)


async def _safe_json(request: Request) -> Dict[str, Any]:
    """Safely extract JSON payload from request"""
    try:
        return await request.json()
    except Exception:
        return {}


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """GitHub Actions webhook endpoint"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "github", x_github_event, payload)
    return {"status": "accepted", "source": "github", "event_type": x_github_event or "unknown"}


@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_event: Optional[str] = Header(None),
    x_gitlab_token: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """GitLab CI webhook endpoint"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "gitlab", x_gitlab_event, payload)
    return {"status": "accepted", "source": "gitlab", "event_type": x_gitlab_event or "unknown"}


@router.post("/jenkins")
async def jenkins_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """Jenkins webhook endpoint (Notification plugin)"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "jenkins", None, payload)
    return {"status": "accepted", "source": "jenkins"}


@router.post("/circleci")
async def circleci_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    circleci_signature: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """CircleCI v2 webhook endpoint"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "circleci", payload.get("type"), payload)
    return {"status": "accepted", "source": "circleci"}


@router.post("/argocd")
async def argocd_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """ArgoCD application sync webhook"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "argocd", None, payload)
    return {"status": "accepted", "source": "argocd"}


@router.post("/bitbucket")
async def bitbucket_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_event_key: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """Bitbucket Pipelines webhook endpoint"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "bitbucket", x_event_key, payload)
    return {"status": "accepted", "source": "bitbucket", "event_type": x_event_key or "unknown"}


@router.post("/aws")
async def aws_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, str]:
    """AWS CodePipeline webhook endpoint (via SNS/CloudWatch)"""
    payload = await _safe_json(request)
    background_tasks.add_task(_process_webhook, db, "aws", None, payload)
    return {"status": "accepted", "source": "aws"}
