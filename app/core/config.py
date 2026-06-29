from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE Settings is instantiated
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings(BaseSettings):
    model_config = {"extra": "ignore"}  # Ignore extra environment variables
    
    # App
    APP_NAME: str = "Pipelynx"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # MongoDB
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("DB_NAME", "pipelynx")
    
    # PostgreSQL / TimescaleDB (hybrid time-series store, behind feature flag)
    TIMESCALE_ENABLED: bool = os.getenv("TIMESCALE_ENABLED", "false").lower() in {"1", "true", "yes"}
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "pipelynx")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "pipelynx")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "pipelynx_metrics")
    # Optional: full DATABASE_URL overrides individual components (e.g., for Neon/Supabase/RDS).
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    @property
    def POSTGRES_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Emergent LLM Key (universal key for OpenAI/Anthropic/Gemini via emergentintegrations)
    EMERGENT_LLM_KEY: str = os.getenv("EMERGENT_LLM_KEY", "")
    
    # Alerting / Notifications
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "alerts@pipelynx.io")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Pipelynx Alerts")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    
    # Note: Removed Config class as model_config is used instead

settings = Settings()
