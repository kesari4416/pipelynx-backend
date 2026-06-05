from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

# MongoDB models use Pydantic for validation

class User(BaseModel):
    """User model for MongoDB"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    organization_id: str
    role: str = "member"  # admin, member, viewer
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Organization(BaseModel):
    """Organization model for MongoDB (multi-tenant)"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str  # URL-friendly identifier
    plan: str = "free"  # free, pro, enterprise
    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Integration(BaseModel):
    """CI/CD Integration configuration model"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    type: str  # github, gitlab, jenkins, argocd, circleci, aws, bitbucket
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)  # API keys, webhooks, etc.
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Pipeline(BaseModel):
    """Pipeline configuration model"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    integration_id: str
    name: str
    repository: str
    branch: Optional[str] = None
    external_id: str  # ID from the CI/CD platform
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlertRule(BaseModel):
    """Alert rule configuration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    condition: Dict[str, Any]  # failure, duration_threshold, etc.
    channels: List[str] = []  # email, slack, pagerduty
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PipelineRun(BaseModel):
    """Pipeline run record - normalized across all CI/CD platforms"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    integration_id: str
    pipeline_id: Optional[str] = None  # May be linked to a Pipeline document
    
    # Source info
    source: str  # github, gitlab, jenkins, etc.
    external_id: str  # Run ID from the source system
    external_url: Optional[str] = None  # Link back to source
    
    # Run details
    name: str  # Workflow/Job name
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    author: Optional[str] = None
    trigger: Optional[str] = None  # push, pull_request, schedule, manual
    
    # Status
    status: str  # queued, running, success, failure, cancelled, skipped
    conclusion: Optional[str] = None  # Detailed result
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Logs and errors
    error_message: Optional[str] = None
    log_summary: Optional[str] = None  # AI-generated (Phase 4)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
