from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.schemas.pipeline import (
    PipelineCreate,
    PipelineResponse,
    IntegrationCreate,
    IntegrationResponse,
    PipelineRunResponse
)
from app.models.mongodb import Pipeline, Integration
from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_active_user, get_current_org
from app.services.setup_guides import build_setup_guide
from app.services.polling_service import sync_integration

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])

# ============ Integrations ============

@router.post("/integrations", response_model=IntegrationResponse)
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: dict = Depends(get_current_active_user),
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """Create a new CI/CD integration (gated by plan integrations_max)."""
    from app.services.entitlements import enforce_integration_count
    await enforce_integration_count(db, org["id"])

    integration = Integration(
        organization_id=org["id"],
        type=integration_data.type,
        name=integration_data.name,
        config=integration_data.config
    )
    
    integration_dict = integration.model_dump()
    integration_dict['created_at'] = integration_dict['created_at'].isoformat()
    integration_dict['updated_at'] = integration_dict['updated_at'].isoformat()
    
    await db.integrations.insert_one(integration_dict)
    return IntegrationResponse(**integration_dict)

@router.get("/integrations", response_model=List[IntegrationResponse])
async def list_integrations(
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """List all integrations for the organization"""
    integrations = await db.integrations.find(
        {"organization_id": org["id"]},
        {"_id": 0}
    ).to_list(100)
    return [IntegrationResponse(**integration) for integration in integrations]


@router.get("/integrations/{integration_id}/setup-guide")
async def integration_setup_guide(
    integration_id: str,
    request: Request,
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Return a structured, copy-paste setup guide for connecting this integration."""
    integration = await db.integrations.find_one(
        {"id": integration_id, "organization_id": org["id"]},
        {"_id": 0},
    )
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    # Honour the X-Forwarded-Proto/Host that the K8s ingress / load balancer sets,
    # so the webhook URL shown to the user is the public domain — not localhost.
    fwd_proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    fwd_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = f"{fwd_proto}://{fwd_host}" if fwd_host else None
    guide = build_setup_guide(integration, base_url=base_url)
    guide["integration"] = {
        "id": integration["id"],
        "type": integration["type"],
        "name": integration["name"],
        "config": {
            "connection_mode": (integration.get("config") or {}).get("connection_mode", "webhook"),
            "last_synced_at": (integration.get("config") or {}).get("last_synced_at"),
            "last_sync_count": (integration.get("config") or {}).get("last_sync_count"),
        },
    }
    return guide


@router.post("/integrations/{integration_id}/sync")
async def integration_sync_now(
    integration_id: str,
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Manually trigger a one-shot poll of the integration (pull-mode only)."""
    integration = await db.integrations.find_one(
        {"id": integration_id, "organization_id": org["id"]},
        {"_id": 0},
    )
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    if (integration.get("config") or {}).get("connection_mode") != "pull":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This integration is in webhook mode. Configure pull mode (with an API token + repositories/jobs) to use Sync.",
        )
    return await sync_integration(db, integration)


@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_active_user),
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Delete an integration (org-scoped)."""
    result = await db.integrations.delete_one(
        {"id": integration_id, "organization_id": org["id"]},
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return {"status": "deleted", "id": integration_id}

# ============ Pipelines ============

@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    current_user: dict = Depends(get_current_active_user),
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """Create a new pipeline"""
    # Verify integration exists
    integration = await db.integrations.find_one({
        "id": pipeline_data.integration_id,
        "organization_id": org["id"]
    })
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    pipeline = Pipeline(
        organization_id=org["id"],
        integration_id=pipeline_data.integration_id,
        name=pipeline_data.name,
        repository=pipeline_data.repository,
        branch=pipeline_data.branch,
        external_id=pipeline_data.external_id
    )
    
    pipeline_dict = pipeline.model_dump()
    pipeline_dict['created_at'] = pipeline_dict['created_at'].isoformat()
    pipeline_dict['updated_at'] = pipeline_dict['updated_at'].isoformat()
    
    await db.pipelines.insert_one(pipeline_dict)
    return PipelineResponse(**pipeline_dict)

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """List all pipelines for the organization"""
    pipelines = await db.pipelines.find(
        {"organization_id": org["id"]},
        {"_id": 0}
    ).to_list(1000)
    return [PipelineResponse(**pipeline) for pipeline in pipelines]

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    org: dict = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """Get pipeline details"""
    pipeline = await db.pipelines.find_one({
        "id": pipeline_id,
        "organization_id": org["id"]
    }, {"_id": 0})
    
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found"
        )
    
    return PipelineResponse(**pipeline)
