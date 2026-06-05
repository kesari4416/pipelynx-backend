from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.core.security import decode_access_token
from app.db.mongodb import get_mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_org(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
) -> Dict[str, Any]:
    """Get current user's organization"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with any organization"
        )
    
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org
