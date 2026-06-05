"""
Billing intent + region detection API.

Endpoints:
  GET  /api/v1/billing/region       — public; detects region from IP / Accept-Language
  GET  /api/v1/billing/plans        — public; plan catalog
  GET  /api/v1/billing/subscription — authed; org's current subscription state
  POST /api/v1/billing/intent       — authed; record intent to upgrade
  POST /api/v1/billing/cancel       — authed; cancel current intent / subscription
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_org
from app.db.mongodb import get_mongodb
from app.services.billing_service import PLANS, BillingService, detect_region

router = APIRouter(prefix="/billing", tags=["Billing"])


# ── Request / response schemas ───────────────────────────────────────────────
class IntentRequest(BaseModel):
    plan: str = Field(..., description="One of: free, basic, business, enterprise")
    billing_cycle: str = Field("monthly", description="monthly | yearly")
    seats: int = Field(1, ge=1)
    currency: Optional[str] = Field(None, description="USD | INR. Auto-detected if omitted.")


# ── Public endpoints ─────────────────────────────────────────────────────────
@router.get("/region")
async def get_region(request: Request) -> Dict[str, str]:
    """
    Detect the caller's billing region from CDN-provided country header and the
    browser's Accept-Language. Frontend uses this to show the right currency
    and pre-select Stripe (global) vs Razorpay (India).
    """
    # Cloudflare and most CDNs forward country in CF-IPCountry; fall back to X-Country.
    country = (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-country")
        or request.headers.get("x-vercel-ip-country")
    )
    accept_lang = request.headers.get("accept-language")
    return detect_region(country, accept_lang)


@router.get("/plans")
async def list_plans() -> Dict[str, Any]:
    """Public plan catalog — used by the pricing page to render server-driven plan data."""
    return {"plans": list(PLANS.values())}


# ── Authenticated endpoints ──────────────────────────────────────────────────
@router.get("/subscription")
async def get_subscription(
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Return the current org's subscription state (defaults to free if none)."""
    return await BillingService.get_subscription(db, org["id"])


@router.get("/limits")
async def get_limits(
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """
    Return the org's current plan limits + live usage counters.
    Frontend uses this to render progress bars and "X / Y used" badges.
    """
    from app.services.entitlements import get_limits as _get_limits
    from datetime import datetime as _dt, timezone as _tz

    limits = await _get_limits(db, org["id"])
    integrations_used = await db.integrations.count_documents({"organization_id": org["id"]})
    users_used = await db.users.count_documents({"organization_id": org["id"]})

    today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
    ai_today = await db.ai_usage.find_one(
        {"organization_id": org["id"], "date": today}, {"_id": 0, "count": 1}
    )
    return {
        "plan": limits["plan"],
        "limits": {k: v for k, v in limits.items() if k != "plan"},
        "usage": {
            "integrations": integrations_used,
            "users": users_used,
            "ai_analyses_today": (ai_today or {}).get("count", 0),
        },
    }


@router.post("/intent", status_code=status.HTTP_201_CREATED)
async def record_intent(
    payload: IntentRequest,
    request: Request,
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """
    Record the user's intent to upgrade. No money changes hands here — the
    operator follows up with a manual invoice (Stripe / Razorpay automation
    will replace this in a later phase).
    """
    # Auto-detect currency / provider if not specified by client
    region = detect_region(
        request.headers.get("cf-ipcountry") or request.headers.get("x-country"),
        request.headers.get("accept-language"),
    )
    currency = (payload.currency or region["currency"]).upper()
    if currency not in {"USD", "INR"}:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {currency}")
    provider = "razorpay" if currency == "INR" else "stripe"

    try:
        sub = await BillingService.set_intent(
            db,
            organization_id=org["id"],
            plan=payload.plan,
            billing_cycle=payload.billing_cycle,
            currency=currency,
            provider=provider,
            seats=payload.seats,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "subscription": sub,
        "next_step": _next_step_message(sub),
    }


@router.post("/cancel")
async def cancel_subscription(
    org: Dict[str, Any] = Depends(get_current_org),
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
) -> Dict[str, Any]:
    """Cancel the current subscription / intent."""
    return await BillingService.cancel(db, org["id"])


def _next_step_message(sub: Dict[str, Any]) -> str:
    """Human-readable next step shown in the UI after recording intent."""
    plan = sub.get("plan")
    sub_status = sub.get("status")
    if plan == "free":
        return "Your Free plan is active. Upgrade anytime."
    if plan == "enterprise":
        return "Our sales team will contact you within 1 business day."
    if sub_status == "intent":
        return "We'll send your invoice via email within 24 hours."
    return ""
