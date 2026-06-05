from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class PipelineCreate(BaseModel):
    """Create pipeline schema"""
    integration_id: str
    name: str
    repository: str
    branch: Optional[str] = None
    external_id: str

class PipelineResponse(BaseModel):
    """Pipeline response schema"""
    id: str
    organization_id: str
    integration_id: str
    name: str
    repository: str
    branch: Optional[str] = None
    external_id: str
    is_active: bool
    created_at: datetime

class PipelineRunResponse(BaseModel):
    """Pipeline run response schema"""
    id: str
    pipeline_id: str
    run_number: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    author: Optional[str] = None
    error_message: Optional[str] = None
    log_summary: Optional[str] = None

class IntegrationCreate(BaseModel):
    """Create integration schema"""
    type: str  # github, gitlab, jenkins, etc.
    name: str
    config: Dict[str, Any]

class IntegrationResponse(BaseModel):
    """Integration response schema"""
    id: str
    organization_id: str
    type: str
    name: str
    is_active: bool
    created_at: datetime
