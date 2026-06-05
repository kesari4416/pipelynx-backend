from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid

from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.mongodb import User, Organization
from app.schemas.auth import UserRegister, UserLogin

class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def register_user(user_data: UserRegister, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Register a new user and organization"""
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create organization
        org_slug = user_data.organization_name.lower().replace(" ", "-")
        organization = Organization(
            name=user_data.organization_name,
            slug=org_slug
        )
        org_dict = organization.model_dump()
        org_dict['created_at'] = org_dict['created_at'].isoformat()
        org_dict['updated_at'] = org_dict['updated_at'].isoformat()
        await db.organizations.insert_one(org_dict)
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            organization_id=organization.id,
            role="admin"  # First user is admin
        )
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        user_dict['updated_at'] = user_dict['updated_at'].isoformat()
        await db.users.insert_one(user_dict)

        # Create a default free subscription record so plan-gating has explicit state.
        # Idempotent in case of registration retries — we always upsert.
        from datetime import datetime as _dt, timezone as _tz
        now_iso = _dt.now(_tz.utc).isoformat()
        await db.subscriptions.update_one(
            {"organization_id": organization.id},
            {
                "$setOnInsert": {
                    "organization_id": organization.id,
                    "plan": "free",
                    "plan_name": "Free",
                    "billing_cycle": None,
                    "seats": 1,
                    "currency": "USD",
                    "provider": None,
                    "status": "active",
                    "price_per_seat": 0,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
            },
            upsert=True,
        )

        # Create access token
        access_token = create_access_token(data={"sub": user.id, "org_id": organization.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "organization_id": organization.id,
                "role": user.role
            }
        }
    
    @staticmethod
    async def login_user(login_data: UserLogin, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
        """Login user and return access token"""
        # Find user
        user = await db.users.find_one({"email": login_data.email}, {"_id": 0})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user["id"], "org_id": user["organization_id"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "organization_id": user["organization_id"],
                "role": user["role"]
            }
        }
