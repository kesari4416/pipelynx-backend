from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.core.config import settings
from app.db.mongodb import connect_mongodb, close_mongodb, mongo_conn
from app.db.redis import connect_redis, close_redis
from app.services.polling_service import polling_loop

# Import API routers
from app.api.v1 import auth, organizations, pipelines, webhooks, runs, metrics, ai, alerts, admin, billing

# Load environment variables
ROOT_DIR: Path = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: logging.Logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager - handles startup and shutdown"""
    # Startup
    logger.info("Starting Pipelynx API...")
    await connect_mongodb()
    await connect_redis()

    # TimescaleDB — only initialize when the feature flag is on.
    # The hybrid time-series store is opt-in to keep dev / preview envs lightweight.
    if settings.TIMESCALE_ENABLED:
        try:
            from app.db.postgres import init_postgres_db
            await init_postgres_db()
            logger.info("TimescaleDB initialized (hybrid time-series store ON)")
        except Exception as ts_err:
            logger.warning(f"TimescaleDB init failed (continuing without it): {ts_err}")
    else:
        logger.info("TimescaleDB feature flag is OFF — running MongoDB-only mode")

    logger.info("Pipelynx API started successfully!")

    # Background polling task — pulls runs from pull-mode integrations every 60s.
    polling_task = asyncio.create_task(polling_loop(lambda: mongo_conn.db))

    yield

    # Shutdown
    logger.info("Shutting down Pipelynx API...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await close_mongodb()
    await close_redis()
    logger.info("Pipelynx API shut down successfully!")

# Create FastAPI app
app: FastAPI = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(pipelines.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
app.include_router(runs.router, prefix=settings.API_V1_PREFIX)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(billing.router, prefix=settings.API_V1_PREFIX)

# Health check endpoint
@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint - returns service status"""
    return {
        "status": "healthy",
        "service": "pipelynx-api",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/api")
async def root() -> Dict[str, str]:
    """Root endpoint - returns API welcome message"""
    return {
        "message": "Welcome to Pipelynx API",
        "version": "1.0.0",
        "docs": "/docs"
    }
