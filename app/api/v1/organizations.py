from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.schemas.organization import OrganizationResponse
from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_active_user, get_current_org

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    org: dict = Depends(get_current_org)
):
    """Get current user's organization"""
    return OrganizationResponse(**org)
