"""
Seed a super-admin user with full Enterprise-plan access.

Usage:
    cd /var/www/pipelynx/backend         # production
    source .venv/bin/activate
    python -m scripts.seed_admin

    # or with explicit overrides
    ADMIN_EMAIL=foo@bar.com ADMIN_PASSWORD=secret ADMIN_NAME="Foo" python -m scripts.seed_admin

Idempotent — re-running updates the existing user's password and ensures
the org has an active Enterprise subscription.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure we can import the app package when run as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

# Load backend/.env so MONGO_URL/DB_NAME are available when run from CLI
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Defaults — override via env vars
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@sparkcurv.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Aiden@1996")
ADMIN_NAME = os.environ.get("ADMIN_NAME", "Sparkcurv Admin")
ORG_NAME = os.environ.get("ADMIN_ORG_NAME", "Sparkcurv Technologies")
ADMIN_PLAN = os.environ.get("ADMIN_PLAN", "enterprise")  # enterprise = unlimited everything

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "pipelynx")


async def main() -> None:
    # Local imports so MONGO_URL is read first
    from app.core.security import get_password_hash  # noqa: E402
    from app.models.mongodb import Organization, User  # noqa: E402

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    now_iso = datetime.now(timezone.utc).isoformat()

    # ── 1. Find or create the organization ────────────────────────────────
    existing_user = await db.users.find_one({"email": ADMIN_EMAIL})
    if existing_user:
        org_id = existing_user["organization_id"]
        org = await db.organizations.find_one({"id": org_id})
        if not org:
            org_doc = Organization(name=ORG_NAME).model_dump()
            org_doc["id"] = org_id
            await db.organizations.insert_one(org_doc)
        print(f"✓ Existing user found — org_id={org_id}")
    else:
        org = await db.organizations.find_one({"name": ORG_NAME})
        if org:
            org_id = org["id"]
        else:
            org = Organization(name=ORG_NAME)
            await db.organizations.insert_one(org.model_dump())
            org_id = org.id
        print(f"✓ Organization ready — id={org_id}")

    # ── 2. Create or update the admin user ────────────────────────────────
    hashed = get_password_hash(ADMIN_PASSWORD)
    user_doc = {
        "email": ADMIN_EMAIL,
        "full_name": ADMIN_NAME,
        "hashed_password": hashed,
        "organization_id": org_id,
        "role": "admin",
        "is_active": True,
        "updated_at": now_iso,
    }
    if existing_user:
        await db.users.update_one({"email": ADMIN_EMAIL}, {"$set": user_doc})
        print(f"✓ Updated existing admin — email={ADMIN_EMAIL}")
    else:
        user = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            hashed_password=hashed,
            organization_id=org_id,
            role="admin",
        )
        doc = user.model_dump()
        doc["created_at"] = now_iso
        doc["updated_at"] = now_iso
        await db.users.insert_one(doc)
        print(f"✓ Created admin user — email={ADMIN_EMAIL}")

    # ── 3. Set Enterprise plan with active status (full access) ───────────
    sub_doc = {
        "organization_id": org_id,
        "plan": ADMIN_PLAN,
        "plan_name": ADMIN_PLAN.capitalize(),
        "billing_cycle": "yearly",
        "seats": 999,
        "currency": "USD",
        "provider": "manual",
        "status": "active",
        "price_per_seat": 0,
        "updated_at": now_iso,
    }
    existing_sub = await db.subscriptions.find_one({"organization_id": org_id})
    if existing_sub:
        await db.subscriptions.update_one({"organization_id": org_id}, {"$set": sub_doc})
    else:
        sub_doc["created_at"] = now_iso
        await db.subscriptions.insert_one(sub_doc)
    print(f"✓ Subscription set — plan={ADMIN_PLAN} status=active (full access)")

    print()
    print("=" * 60)
    print("ADMIN SEED COMPLETE")
    print("=" * 60)
    print(f"  Email    : {ADMIN_EMAIL}")
    print(f"  Password : {ADMIN_PASSWORD}")
    print(f"  Plan     : {ADMIN_PLAN} (unlimited access)")
    print(f"  Org ID   : {org_id}")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
