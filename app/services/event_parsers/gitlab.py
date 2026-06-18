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
        return object_kind in ("pipeline", "build", "job", "push")
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        object_kind = payload.get("object_kind", "")
        if object_kind == "pipeline":
            return self._parse_pipeline(payload)
        if object_kind in ("build", "job"):
            return self._parse_job(payload)
        if object_kind == "push":
            return self._parse_push(payload)
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

    def _parse_push(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a GitLab `push` event (object_kind=push) — one run per push."""
        # Branch deletions report `after = 0000…` — ignore them.
        after = payload.get("after", "")
        if not after or set(after) == {"0"}:
            return None

        project = payload.get("project") or payload.get("repository") or {}
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        commits = payload.get("commits") or []
        head = commits[-1] if commits else {}
        head_id = head.get("id") or after
        author = head.get("author") or {}

        started_at = self.parse_iso_datetime(head.get("timestamp"))
        return {
            "source": self.source,
            "external_id": f"push:{head_id}",
            "external_url": head.get("url"),
            "name": f"push to {branch}" if branch else "push",
            "repository": project.get("path_with_namespace") or project.get("name"),
            "branch": branch,
            "commit_sha": head_id,
            "commit_message": head.get("message"),
            "author": (
                author.get("name")
                or payload.get("user_username")
                or payload.get("user_name")
            ),
            "trigger": "push",
            "status": "success",
            "conclusion": "success",
            "started_at": started_at,
            "completed_at": started_at,
            "duration_seconds": 0,
            "metadata": {
                "ref": ref,
                "commits_count": payload.get("total_commits_count") or len(commits),
                "event_type": "push",
            },
        }
