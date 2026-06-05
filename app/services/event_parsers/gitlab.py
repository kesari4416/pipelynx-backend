"""GitLab CI event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class GitLabEventParser(BaseEventParser):
    """Parser for GitLab CI pipeline events"""
    
    source = "gitlab"
    
    STATUS_MAP = {
        "created": "queued",
        "waiting_for_resource": "queued",
        "preparing": "queued",
        "pending": "queued",
        "running": "running",
        "success": "success",
        "failed": "failure",
        "canceled": "cancelled",
        "cancelled": "cancelled",
        "skipped": "skipped",
        "manual": "queued",
        "scheduled": "queued",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        object_kind = payload.get("object_kind", "")
        return object_kind in ("pipeline", "build", "job")
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        object_kind = payload.get("object_kind", "")
        if object_kind == "pipeline":
            return self._parse_pipeline(payload)
        if object_kind in ("build", "job"):
            return self._parse_job(payload)
        return None
    
    def _parse_pipeline(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        attrs = payload.get("object_attributes", {})
        project = payload.get("project", {})
        commit = payload.get("commit", {})
        user = payload.get("user", {})
        
        gl_status = attrs.get("status", "")
        status = self.STATUS_MAP.get(gl_status, "running")
        
        started_at = self.parse_iso_datetime(attrs.get("created_at"))
        finished_at = self.parse_iso_datetime(attrs.get("finished_at"))
        
        return {
            "source": self.source,
            "external_id": str(attrs.get("id", "")),
            "external_url": attrs.get("url"),
            "name": f"pipeline-{attrs.get('id', '')}",
            "repository": project.get("path_with_namespace") or project.get("name"),
            "branch": attrs.get("ref"),
            "commit_sha": attrs.get("sha") or commit.get("id"),
            "commit_message": commit.get("message"),
            "author": user.get("username") or user.get("name"),
            "trigger": attrs.get("source"),
            "status": status,
            "conclusion": gl_status,
            "started_at": started_at,
            "completed_at": finished_at,
            "duration_seconds": attrs.get("duration") or self.calculate_duration(started_at, finished_at),
            "metadata": {
                "pipeline_iid": attrs.get("iid"),
                "stages": attrs.get("stages", []),
                "event_type": "pipeline",
            },
        }
    
    def _parse_job(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        gl_status = payload.get("build_status") or payload.get("status", "")
        status = self.STATUS_MAP.get(gl_status, "running")
        
        started_at = self.parse_iso_datetime(payload.get("build_started_at"))
        finished_at = self.parse_iso_datetime(payload.get("build_finished_at"))
        
        return {
            "source": self.source,
            "external_id": str(payload.get("build_id") or payload.get("id", "")),
            "name": payload.get("build_name") or payload.get("name") or "job",
            "repository": (payload.get("project") or {}).get("path_with_namespace"),
            "branch": payload.get("ref"),
            "commit_sha": payload.get("sha"),
            "status": status,
            "conclusion": gl_status,
            "started_at": started_at,
            "completed_at": finished_at,
            "duration_seconds": payload.get("build_duration") or self.calculate_duration(started_at, finished_at),
            "metadata": {"event_type": "job"},
        }
