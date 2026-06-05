"""
Admin / operational endpoints — currently exposes infrastructure health.

Restricted to authenticated org members. Returns:
- TimescaleDB feature-flag state and reachability
- Row counts (when reachable) for the org

This is intentionally lightweight; deeper admin tooling is out of scope for MVP.
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict

from app.core.dependencies import get_current_org
from app.db import postgres as ts_db
from app.services.timescale_service import TimescaleService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/timescale/status")
async def timescale_status(org: Dict[str, Any] = Depends(get_current_org)) -> Dict[str, Any]:
    """Report TimescaleDB feature-flag state and connection health."""
    health = await ts_db.healthcheck()
    row_count = await TimescaleService.count_runs(org["id"]) if health.get("reachable") else None
    return {
        **health,
        "org_pipeline_runs_in_timescale": row_count,
        "dual_write": "active" if health.get("reachable") else "inactive",
    }
