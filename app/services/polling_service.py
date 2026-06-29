"""
Polling service — pulls pipeline runs from CI/CD platforms over their REST APIs.

Useful when inbound webhooks cannot be configured (private Jenkins behind firewall,
shared GitLab instances, audit-only access, etc.). Runs in a background asyncio
loop and pushes results through the same PipelineRunService.ingest_event pipeline
the webhooks use, so all downstream behaviour (DORA metrics, alerting, Timescale
dual-write) is identical.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.pipeline_service import PipelineRunService

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60
REQUEST_TIMEOUT = 20


# ============ GitHub Actions ============

async def _poll_github(db: AsyncIOMotorDatabase, integration: Dict[str, Any]) -> int:
    cfg = integration.get("config") or {}
    token = cfg.get("api_token") or cfg.get("pat")
    repos = cfg.get("repositories") or []  # ["owner/repo", ...]
    if not token or not repos:
        return 0

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    ingested = 0
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for repo in repos:
            url = f"https://api.github.com/repos/{repo}/actions/runs"
            try:
                resp = await client.get(url, headers=headers, params={"per_page": 20})
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("GitHub poll failed for %s: %s", repo, e)
                continue

            for run in data.get("workflow_runs", []):
                payload = {
                    "workflow_run": run,
                    "repository": {"full_name": repo},
                }
                try:
                    result = await PipelineRunService.ingest_event(
                        db=db, source="github", event_type="workflow_run", payload=payload,
                    )
                    if result is not None:
                        ingested += 1
                except Exception as ingest_err:
                    logger.warning("GitHub ingest failed for run %s: %s", run.get("id"), ingest_err)
    return ingested


# ============ GitLab CI ============

async def _poll_gitlab(db: AsyncIOMotorDatabase, integration: Dict[str, Any]) -> int:
    cfg = integration.get("config") or {}
    token = cfg.get("api_token") or cfg.get("pat")
    base_url = (cfg.get("base_url") or "https://gitlab.com").rstrip("/")
    projects = cfg.get("project_ids") or []  # numeric IDs or namespaced paths
    if not token or not projects:
        return 0

    headers = {"PRIVATE-TOKEN": token}
    ingested = 0
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for project in projects:
            # URL-encode namespaced project paths
            project_ref = str(project).replace("/", "%2F") if "/" in str(project) else str(project)
            url = f"{base_url}/api/v4/projects/{project_ref}/pipelines"
            try:
                resp = await client.get(url, headers=headers, params={"per_page": 20})
                resp.raise_for_status()
                pipelines = resp.json()
            except Exception as e:
                logger.warning("GitLab poll failed for %s: %s", project, e)
                continue

            # Fetch project name once for repository field
            project_path = str(project)
            try:
                proj_resp = await client.get(f"{base_url}/api/v4/projects/{project_ref}", headers=headers)
                if proj_resp.status_code == 200:
                    project_path = proj_resp.json().get("path_with_namespace", project_path)
            except Exception:
                pass

            for pl in pipelines:
                payload = {
                    "object_kind": "pipeline",
                    "object_attributes": {
                        "id": pl.get("id"),
                        "status": pl.get("status"),
                        "ref": pl.get("ref"),
                        "sha": pl.get("sha"),
                        "source": pl.get("source", "push"),
                        "duration": pl.get("duration"),
                        "created_at": pl.get("created_at"),
                        "finished_at": pl.get("updated_at"),
                        "url": pl.get("web_url"),
                    },
                    "project": {"path_with_namespace": project_path},
                    "commit": {"id": pl.get("sha"), "message": ""},
                    "user": {"username": (pl.get("user") or {}).get("username", "unknown")},
                }
                try:
                    result = await PipelineRunService.ingest_event(
                        db=db, source="gitlab", event_type="Pipeline Hook", payload=payload,
                    )
                    if result is not None:
                        ingested += 1
                except Exception as ingest_err:
                    logger.warning("GitLab ingest failed for pipeline %s: %s", pl.get("id"), ingest_err)
    return ingested


# ============ Jenkins ============

async def _poll_jenkins(db: AsyncIOMotorDatabase, integration: Dict[str, Any]) -> int:
    cfg = integration.get("config") or {}
    base_url = (cfg.get("base_url") or "").rstrip("/")
    user = cfg.get("username") or cfg.get("user")
    token = cfg.get("api_token") or cfg.get("pat")
    jobs = cfg.get("jobs") or []  # ["my-job", "folder/job/sub-job"]
    if not base_url or not user or not token or not jobs:
        return 0

    auth = (user, token)
    ingested = 0
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, auth=auth) as client:
        for job in jobs:
            # Support folder paths (Jenkins URLs use /job/<name>/ for each segment)
            job_url_path = "/job/" + "/job/".join(job.split("/"))
            url = f"{base_url}{job_url_path}/api/json"
            params = {"tree": "name,builds[number,result,timestamp,duration,url,actions[lastBuiltRevision[SHA1,branch[name]]]]"}
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("Jenkins poll failed for job %s: %s", job, e)
                continue

            job_name = data.get("name") or job.split("/")[-1]
            for build in (data.get("builds") or [])[:20]:
                # Jenkins Notification-plugin compatible payload
                status_str = (build.get("result") or "RUNNING")
                branch = ""
                commit = ""
                for action in (build.get("actions") or []):
                    rev = (action or {}).get("lastBuiltRevision") or {}
                    if rev:
                        commit = rev.get("SHA1", "") or commit
                        branches = rev.get("branch") or []
                        if branches:
                            branch = (branches[0].get("name") or "").replace("refs/remotes/origin/", "")
                            break
                payload = {
                    "name": job_name,
                    "build": {
                        "number": build.get("number"),
                        "phase": "COMPLETED" if build.get("result") else "STARTED",
                        "status": status_str,
                        "timestamp": build.get("timestamp"),
                        "duration": build.get("duration"),
                        "full_url": build.get("url"),
                        "scm": {"branch": branch or "main", "commit": commit},
                    },
                }
                try:
                    result = await PipelineRunService.ingest_event(
                        db=db, source="jenkins", event_type=None, payload=payload,
                    )
                    if result is not None:
                        ingested += 1
                except Exception as ingest_err:
                    logger.warning("Jenkins ingest failed for build %s/%s: %s", job, build.get("number"), ingest_err)
    return ingested


# ============ Dispatcher ============

_POLLERS = {
    "github": _poll_github,
    "gitlab": _poll_gitlab,
    "jenkins": _poll_jenkins,
}


async def sync_integration(db: AsyncIOMotorDatabase, integration: Dict[str, Any]) -> Dict[str, Any]:
    """Force a one-shot sync for a single integration. Returns a status report."""
    platform = (integration.get("type") or "").lower()
    poller = _POLLERS.get(platform)
    if not poller:
        return {"ok": False, "platform": platform, "reason": "polling-not-supported"}

    started = datetime.now(timezone.utc)
    try:
        count = await poller(db, integration)
        await db.integrations.update_one(
            {"id": integration["id"]},
            {"$set": {"config.last_synced_at": started.isoformat(), "config.last_sync_count": count}},
        )
        return {"ok": True, "platform": platform, "ingested": count, "synced_at": started.isoformat()}
    except Exception as e:
        logger.error("sync_integration failed for %s: %s", platform, e, exc_info=True)
        return {"ok": False, "platform": platform, "reason": str(e)}


async def _poll_all_pull_integrations(db: AsyncIOMotorDatabase) -> None:
    """Iterate all integrations with connection_mode == 'pull' and sync them."""
    cursor = db.integrations.find(
        {"is_active": True, "config.connection_mode": "pull"},
        {"_id": 0},
    )
    integrations: List[Dict[str, Any]] = await cursor.to_list(500)
    if not integrations:
        return
    logger.info("Polling %d pull-mode integrations…", len(integrations))
    results = await asyncio.gather(
        *[sync_integration(db, i) for i in integrations],
        return_exceptions=True,
    )
    success = sum(1 for r in results if isinstance(r, dict) and r.get("ok"))
    logger.info("Polling cycle complete: %d/%d succeeded", success, len(integrations))


async def polling_loop(get_db) -> None:
    """Background asyncio task — runs forever, syncing every POLL_INTERVAL_SECONDS."""
    logger.info("Polling loop started (interval=%ds)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            db = get_db()
            if db is not None:
                await _poll_all_pull_integrations(db)
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
            raise
        except Exception as e:
            logger.error("Polling loop iteration failed: %s", e, exc_info=True)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
