"""
Plan-based entitlements & access control.

Every paid feature / quota in Pipelynx is gated through this module. Endpoints
call the `enforce_*` helpers, which raise `HTTPException(402, ...)` with a
machine-readable payload the frontend uses to show an upgrade modal:

    {
        "detail": "Free plan allows 3 integrations. Upgrade to Basic for 10.",
        "required_plan": "basic",
        "current_plan": "free",
        "feature": "integrations_count",
        "limit": 3,
        "current_usage": 3,
    }

Plan limits are the single source of truth advertised on the pricing page —
keep `PLAN_LIMITS` in sync with `PricingPage.jsx` and `billing_service.PLANS`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

# ── Plan limits (mirror of the pricing page) ──────────────────────────────────
# `None` = unlimited
PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "integrations_max": 3,
        "users_max": 1,
        "runs_per_month": 1_000,
        "retention_days": 7,
        "ai_analyses_per_day": 0,           # No AI on Free
        "alert_channels": {"email"},        # Email only
        "anomaly_detection": False,
        "pattern_detection": False,
        "weekly_digest": False,
    },
    "basic": {
        "integrations_max": 10,
        "users_max": 5,
        "runs_per_month": 10_000,
        "retention_days": 30,
        "ai_analyses_per_day": 10,
        "alert_channels": {"email", "slack"},
        "anomaly_detection": False,
        "pattern_detection": False,
        "weekly_digest": False,
    },
    "business": {
        "integrations_max": None,
        "users_max": 25,
        "runs_per_month": 100_000,
        "retention_days": 90,
        "ai_analyses_per_day": None,        # Unlimited
        "alert_channels": {"email", "slack", "webhook", "pagerduty"},
        "anomaly_detection": True,
        "pattern_detection": True,
        "weekly_digest": True,
    },
    "enterprise": {
        "integrations_max": None,
        "users_max": None,
        "runs_per_month": None,
        "retention_days": None,
        "ai_analyses_per_day": None,
        "alert_channels": {"email", "slack", "webhook", "pagerduty", "custom"},
        "anomaly_detection": True,
        "pattern_detection": True,
        "weekly_digest": True,
    },
}

# Plan upgrade ladder — used to pick the cheapest plan that satisfies a limit
_PLAN_ORDER = ["free", "basic", "business", "enterprise"]


def _required_plan_for_channel(channel: str) -> str:
    """Find the cheapest plan that allows the given alert channel."""
    for plan_id in _PLAN_ORDER:
        if channel in PLAN_LIMITS[plan_id]["alert_channels"]:
            return plan_id
    return "enterprise"


def _required_plan_for_feature(feature_key: str) -> str:
    """Find the cheapest plan that enables a boolean feature."""
    for plan_id in _PLAN_ORDER:
        if PLAN_LIMITS[plan_id].get(feature_key):
            return plan_id
    return "enterprise"


def _required_plan_for_limit(field: str, requested: int) -> str:
    """
    Find the cheapest plan whose `field` limit is `>= requested` (or unlimited).
    Used for integrations_max / runs_per_month / ai_analyses_per_day etc.
    """
    for plan_id in _PLAN_ORDER:
        limit = PLAN_LIMITS[plan_id].get(field)
        if limit is None or limit >= requested:
            return plan_id
    return "enterprise"


# ── Plan resolution ───────────────────────────────────────────────────────────
async def get_org_plan(db: AsyncIOMotorDatabase, organization_id: str) -> str:
    """
    Return the active plan id for an org. Defaults to `free` if no subscription
    exists or if the subscription is cancelled.
    """
    sub = await db.subscriptions.find_one(
        {"organization_id": organization_id},
        {"_id": 0, "plan": 1, "status": 1},
    )
    if not sub:
        return "free"
    if sub.get("status") == "cancelled":
        return "free"
    plan = sub.get("plan", "free")
    return plan if plan in PLAN_LIMITS else "free"


async def get_limits(db: AsyncIOMotorDatabase, organization_id: str) -> Dict[str, Any]:
    """Return the resolved limits dict for an org's current plan."""
    plan = await get_org_plan(db, organization_id)
    return {"plan": plan, **PLAN_LIMITS[plan]}


# ── 402 helper ────────────────────────────────────────────────────────────────
def _raise_402(
    *,
    current_plan: str,
    required_plan: str,
    feature: str,
    detail: str,
    limit: Optional[int] = None,
    current_usage: Optional[int] = None,
) -> None:
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "detail": detail,
            "current_plan": current_plan,
            "required_plan": required_plan,
            "feature": feature,
            "limit": limit,
            "current_usage": current_usage,
        },
    )


# ── Enforcement helpers (call these from API handlers) ────────────────────────
async def enforce_integration_count(db: AsyncIOMotorDatabase, organization_id: str) -> None:
    """Block creating a new integration when the org has hit the plan cap."""
    plan = await get_org_plan(db, organization_id)
    limit = PLAN_LIMITS[plan]["integrations_max"]
    if limit is None:
        return
    current = await db.integrations.count_documents({"organization_id": organization_id})
    if current >= limit:
        required = _required_plan_for_limit("integrations_max", current + 1)
        _raise_402(
            current_plan=plan,
            required_plan=required,
            feature="integrations_count",
            limit=limit,
            current_usage=current,
            detail=(
                f"Your {plan.capitalize()} plan is limited to {limit} integration{'s' if limit != 1 else ''}. "
                f"Upgrade to {required.capitalize()} to add more."
            ),
        )


async def enforce_alert_channels(db: AsyncIOMotorDatabase, organization_id: str, channels: list) -> None:
    """Block creating an alert rule that uses a channel outside the plan's allowlist."""
    plan = await get_org_plan(db, organization_id)
    allowed = PLAN_LIMITS[plan]["alert_channels"]
    for ch in channels:
        if ch not in allowed:
            required = _required_plan_for_channel(ch)
            _raise_402(
                current_plan=plan,
                required_plan=required,
                feature="alert_channels",
                detail=(
                    f"The '{ch}' alert channel is not available on the {plan.capitalize()} plan. "
                    f"Upgrade to {required.capitalize()} to unlock it."
                ),
            )


async def enforce_ai_quota(db: AsyncIOMotorDatabase, organization_id: str) -> None:
    """
    Block AI analysis when the org has hit its daily quota.
    Usage is tracked in `ai_usage` collection: {organization_id, date (YYYY-MM-DD), count}.
    """
    plan = await get_org_plan(db, organization_id)
    daily_cap = PLAN_LIMITS[plan]["ai_analyses_per_day"]
    if daily_cap is None:
        return  # Unlimited
    if daily_cap == 0:
        required = _required_plan_for_limit("ai_analyses_per_day", 1)
        _raise_402(
            current_plan=plan,
            required_plan=required,
            feature="ai_analysis",
            detail=(
                f"AI failure analysis is not included in the {plan.capitalize()} plan. "
                f"Upgrade to {required.capitalize()} to unlock it."
            ),
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    usage = await db.ai_usage.find_one(
        {"organization_id": organization_id, "date": today},
        {"_id": 0, "count": 1},
    )
    used = (usage or {}).get("count", 0)
    if used >= daily_cap:
        required = _required_plan_for_limit("ai_analyses_per_day", used + 1)
        _raise_402(
            current_plan=plan,
            required_plan=required,
            feature="ai_analysis",
            limit=daily_cap,
            current_usage=used,
            detail=(
                f"You've used {used}/{daily_cap} AI analyses today on the {plan.capitalize()} plan. "
                f"Upgrade to {required.capitalize()} for higher limits."
            ),
        )


async def record_ai_usage(db: AsyncIOMotorDatabase, organization_id: str) -> None:
    """Increment today's AI usage counter — call after a successful analysis."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await db.ai_usage.update_one(
        {"organization_id": organization_id, "date": today},
        {"$inc": {"count": 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


async def enforce_feature(db: AsyncIOMotorDatabase, organization_id: str, feature_key: str) -> None:
    """
    Generic gate for boolean features (pattern_detection, anomaly_detection, weekly_digest).
    """
    plan = await get_org_plan(db, organization_id)
    if PLAN_LIMITS[plan].get(feature_key):
        return
    required = _required_plan_for_feature(feature_key)
    pretty = feature_key.replace("_", " ")
    _raise_402(
        current_plan=plan,
        required_plan=required,
        feature=feature_key,
        detail=(
            f"{pretty.title()} is not available on the {plan.capitalize()} plan. "
            f"Upgrade to {required.capitalize()} to unlock it."
        ),
    )
