"""
Billing intent service — manages an organization's selected plan and billing region.

This is the **plan-selection state model** that sits in front of any future
Stripe / Razorpay integration. It captures user intent (which plan they want
and which region/currency to bill them in) so the operator can invoice manually
until automated checkout is wired up in a later phase.

State machine for `subscription.status`:
    none → intent → active (set manually by operator once invoice is paid)
                  → cancelled (set by user/operator)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ── Plan catalog (source of truth — frontend keys must match) ─────────────────
PLANS: Dict[str, Dict[str, Any]] = {
    "free": {"id": "free", "name": "Free", "price_usd": 0, "price_inr": 0, "billable": False},
    "basic": {"id": "basic", "name": "Basic", "price_usd": 29, "price_inr": 2400, "billable": True},
    "business": {"id": "business", "name": "Business", "price_usd": 79, "price_inr": 6500, "billable": True},
    "enterprise": {"id": "enterprise", "name": "Enterprise", "price_usd": None, "price_inr": None, "billable": False, "contact_sales": True},
}

# ── Region routing (auto-detect → Stripe vs Razorpay) ─────────────────────────
INDIA_COUNTRY_CODES = {"IN"}
INDIA_LOCALES = {"hi", "hi-in", "en-in", "bn-in", "ta-in", "te-in", "mr-in", "gu-in"}


def detect_region(country_code: Optional[str], accept_language: Optional[str]) -> Dict[str, str]:
    """
    Decide which payment provider + currency to route a user to.

    Inputs:
      - `country_code`: ISO-3166-1 alpha-2 from request header (CF-IPCountry, X-Country, etc.)
      - `accept_language`: browser Accept-Language header

    Returns: `{"region": "IN" | "GLOBAL", "currency": "INR" | "USD", "provider": "razorpay" | "stripe"}`
    """
    cc = (country_code or "").upper().strip()
    al = (accept_language or "").lower().strip()

    is_india = cc in INDIA_COUNTRY_CODES or any(loc in al for loc in INDIA_LOCALES)
    if is_india:
        return {"region": "IN", "currency": "INR", "provider": "razorpay"}
    return {"region": "GLOBAL", "currency": "USD", "provider": "stripe"}


class BillingService:
    """All operations are scoped to an organization."""

    @staticmethod
    async def get_subscription(db: AsyncIOMotorDatabase, organization_id: str) -> Dict[str, Any]:
        """
        Return the org's current subscription document. Defaults to a Free
        subscription if no record exists yet.
        """
        sub = await db.subscriptions.find_one({"organization_id": organization_id}, {"_id": 0})
        if sub:
            return sub
        return {
            "organization_id": organization_id,
            "plan": "free",
            "billing_cycle": None,
            "status": "active",
            "currency": "USD",
            "provider": None,
            "created_at": None,
            "updated_at": None,
        }

    @staticmethod
    async def set_intent(
        db: AsyncIOMotorDatabase,
        organization_id: str,
        plan: str,
        billing_cycle: str,
        currency: str,
        provider: str,
        seats: int = 1,
    ) -> Dict[str, Any]:
        """
        Record the user's intent to upgrade. Operator can flip `status` to
        `active` once payment is collected out-of-band.
        """
        if plan not in PLANS:
            raise ValueError(f"Unknown plan: {plan}")
        if billing_cycle not in {"monthly", "yearly"}:
            raise ValueError(f"Invalid billing_cycle: {billing_cycle}")
        if seats < 1:
            raise ValueError("seats must be >= 1")

        now_iso = datetime.now(timezone.utc).isoformat()
        plan_meta = PLANS[plan]
        is_free = plan == "free"
        is_enterprise = plan == "enterprise"

        # Free → activate immediately. Enterprise → mark sales-contact. Paid → intent.
        if is_free:
            status = "active"
        elif is_enterprise:
            status = "contact_sales"
        else:
            status = "intent"

        doc: Dict[str, Any] = {
            "organization_id": organization_id,
            "plan": plan,
            "plan_name": plan_meta["name"],
            "billing_cycle": billing_cycle,
            "seats": seats,
            "currency": currency,
            "provider": provider,
            "status": status,
            "price_per_seat": plan_meta.get(f"price_{currency.lower()}"),
            "updated_at": now_iso,
        }

        existing = await db.subscriptions.find_one({"organization_id": organization_id}, {"_id": 0})
        if existing:
            await db.subscriptions.update_one(
                {"organization_id": organization_id},
                {"$set": doc},
            )
            doc["created_at"] = existing.get("created_at", now_iso)
        else:
            doc["created_at"] = now_iso
            await db.subscriptions.insert_one(dict(doc))

        logger.info(
            "Billing intent recorded: org=%s plan=%s cycle=%s seats=%s provider=%s status=%s",
            organization_id, plan, billing_cycle, seats, provider, status,
        )
        return doc

    @staticmethod
    async def cancel(db: AsyncIOMotorDatabase, organization_id: str) -> Dict[str, Any]:
        """Mark the current subscription as cancelled (downgrade pending)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.subscriptions.update_one(
            {"organization_id": organization_id},
            {"$set": {"status": "cancelled", "updated_at": now_iso}},
        )
        return await BillingService.get_subscription(db, organization_id)
