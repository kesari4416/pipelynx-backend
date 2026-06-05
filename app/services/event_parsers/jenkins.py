"""Jenkins event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class JenkinsEventParser(BaseEventParser):
    """Parser for Jenkins build events (via Notification plugin or webhook)"""
    
    source = "jenkins"
    
    STATUS_MAP = {
        "SUCCESS": "success",
        "FAILURE": "failure",
        "UNSTABLE": "failure",
        "ABORTED": "cancelled",
        "NOT_BUILT": "skipped",
        "STARTED": "running",
        "QUEUED": "queued",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        # Jenkins payloads typically have a 'build' or 'name' field
        return "build" in payload or "name" in payload
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        build = payload.get("build", {})
        if not build and "number" in payload:
            build = payload
        
        if not build:
            return None
        
        # Initialize with defaults to ensure status is always defined
        status = "running"
        # Jenkins phases: QUEUED, STARTED, COMPLETED, FINALIZED
        phase = build.get("phase", "").upper()
        jenkins_status = build.get("status", "").upper()
        
        if phase == "QUEUED":
            status = "queued"
        elif phase == "STARTED":
            status = "running"
        else:
            status = self.STATUS_MAP.get(jenkins_status, "running")
        
        # Jenkins timestamps are usually in milliseconds since epoch
        timestamp_ms = build.get("timestamp")
        started_at = None
        if timestamp_ms:
            try:
                from datetime import datetime, timezone
                started_at = datetime.fromtimestamp(int(timestamp_ms) / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        duration_ms = build.get("duration")
        duration_seconds = None
        if duration_ms is not None:
            try:
                duration_seconds = float(duration_ms) / 1000
            except (ValueError, TypeError):
                pass
        
        scm = build.get("scm", {})
        
        return {
            "source": self.source,
            "external_id": str(build.get("number", "")),
            "external_url": build.get("full_url") or build.get("url"),
            "name": payload.get("name") or build.get("name") or "build",
            "branch": scm.get("branch"),
            "commit_sha": scm.get("commit"),
            "status": status,
            "conclusion": jenkins_status or None,
            "started_at": started_at,
            "duration_seconds": duration_seconds,
            "metadata": {
                "build_number": build.get("number"),
                "phase": phase,
                "queue_id": build.get("queue_id"),
                "event_type": "build",
            },
        }
