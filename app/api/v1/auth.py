from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.db.mongodb import get_mongodb
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
async def register(
    user_data: UserRegister,
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """Register a new user and organization"""
    return await AuthService.register_user(user_data, db)

@router.post("/login", response_model=dict)
async def login(
    login_data: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_mongodb)
):
    """Login and get access token"""
    return await AuthService.login_user(login_data, db)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(**current_user)
