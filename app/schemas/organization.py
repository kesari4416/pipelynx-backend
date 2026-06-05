from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class OrganizationCreate(BaseModel):
    """Create organization schema"""
    name: str
    slug: str

class OrganizationUpdate(BaseModel):
    """Update organization schema"""
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class OrganizationResponse(BaseModel):
    """Organization response schema"""
    id: str
    name: str
    slug: str
    plan: str
    is_active: bool
    created_at: datetime
