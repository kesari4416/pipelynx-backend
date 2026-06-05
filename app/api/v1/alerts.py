"""Alert Rules and Notifications API"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_org
from app.services.notification_service import (
    SlackNotifier, EmailNotifier, GenericWebhookNotifier
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ============ Schemas ============

class AlertRuleCreate(BaseModel):
    name: str
    condition: Dict[str, Any] = Field(default_factory=dict)
    channels: List[str] = []
    channel_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True


class AlertRuleResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    condition: Dict[str, Any]
    channels: List[str]
    is_active: bool
    created_at: str


# ============ Routes ============

@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    """List all alert rules for the organization"""
    rules = await db.alert_rules.find(
        {"organization_id": org["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return [AlertRuleResponse(**r) for r in rules]


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    """Create a new alert rule (gated by plan alert_channels allowlist)."""
    from app.services.entitlements import enforce_alert_channels
    await enforce_alert_channels(db, org["id"], rule_data.channels)

    rule = {
        "id": str(uuid.uuid4()),
        "organization_id": org["id"],
        "name": rule_data.name,
        "condition": rule_data.condition,
        "channels": rule_data.channels,
        "channel_configs": rule_data.channel_configs,
        "is_active": rule_data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.alert_rules.insert_one(rule)
    return AlertRuleResponse(**rule)


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    """Delete an alert rule"""
    result = await db.alert_rules.delete_one({"id": rule_id, "organization_id": org["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted", "id": rule_id}


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    """Get recent alert dispatches for the organization"""
    # Filter by org via the embedded run document
    history = await db.alert_history.find(
        {"run.organization_id": org["id"]},
        {"_id": 0}
    ).sort("triggered_at", -1).limit(limit).to_list(limit)
    return {"alerts": history, "total": len(history)}


@router.post("/test")
async def test_notification(
    channel: str = Body(..., embed=True),
    config: Dict[str, Any] = Body(..., embed=True),
    org: Dict[str, Any] = Depends(get_current_org),
):
    """
    Send a test notification to verify a channel configuration.
    Body: { "channel": "slack" | "email" | "webhook", "config": { ... } }
    """
    test_alert = {
        "rule_id": "test",
        "rule_name": "Test Alert",
        "run": {
            "name": "Test Pipeline",
            "status": "failure",
            "source": "pipelynx",
            "repository": "your-org/your-repo",
            "branch": "main",
            "duration_seconds": 42,
            "error_message": "This is a test alert from Pipelynx — your notification channel is working!",
            "external_url": "https://pipelynx.io",
        },
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }
    
    success = False
    if channel == "slack":
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url required for slack")
        success = await SlackNotifier.send(webhook_url, test_alert)
    elif channel == "email":
        recipients = config.get("recipients", [])
        if not recipients:
            raise HTTPException(status_code=400, detail="recipients required for email")
        success = await EmailNotifier.send(recipients, test_alert)
    elif channel == "webhook":
        webhook_url = config.get("url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="url required for webhook")
        success = await GenericWebhookNotifier.send(webhook_url, test_alert)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")
    
    return {"success": success, "channel": channel}
