"""CircleCI event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class CircleCIEventParser(BaseEventParser):
    """Parser for CircleCI workflow/job events (v2 webhooks)"""
    
    source = "circleci"
    
    STATUS_MAP = {
        "success": "success",
        "failed": "failure",
        "failing": "failure",
        "error": "failure",
        "canceled": "cancelled",
        "cancelled": "cancelled",
        "unauthorized": "failure",
        "running": "running",
        "on_hold": "queued",
        "queued": "queued",
        "not_run": "skipped",
        "blocked": "queued",
        "not_running": "queued",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        # CircleCI v2 webhooks have a 'type' field
        return payload.get("type") in ("workflow-completed", "job-completed", "workflow-started")
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        wh_type = payload.get("type", "")
        
        if wh_type.startswith("workflow"):
            return self._parse_workflow(payload)
        if wh_type.startswith("job"):
            return self._parse_job(payload)
        return None
    
    def _parse_workflow(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        workflow = payload.get("workflow", {})
        pipeline = payload.get("pipeline", {})
        project = payload.get("project", {})
        
        if not workflow:
            return None
        
        cci_status = workflow.get("status", "")
        status = self.STATUS_MAP.get(cci_status, "running")
        
        started_at = self.parse_iso_datetime(workflow.get("created_at"))
        completed_at = self.parse_iso_datetime(workflow.get("stopped_at"))
        
        vcs = pipeline.get("vcs", {})
        trigger = pipeline.get("trigger", {})
        
        return {
            "source": self.source,
            "external_id": workflow.get("id", ""),
            "external_url": workflow.get("url"),
            "name": workflow.get("name") or "workflow",
            "repository": project.get("name") or vcs.get("origin_repository_url"),
            "branch": vcs.get("branch"),
            "commit_sha": vcs.get("revision"),
            "commit_message": vcs.get("commit", {}).get("subject"),
            "trigger": trigger.get("type"),
            "status": status,
            "conclusion": cci_status,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "metadata": {
                "pipeline_id": pipeline.get("id"),
                "pipeline_number": pipeline.get("number"),
                "event_type": "workflow",
            },
        }
    
    def _parse_job(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        job = payload.get("job", {})
        if not job:
            return None
        
        cci_status = job.get("status", "")
        status = self.STATUS_MAP.get(cci_status, "running")
        
        started_at = self.parse_iso_datetime(job.get("started_at"))
        completed_at = self.parse_iso_datetime(job.get("stopped_at"))
        
        return {
            "source": self.source,
            "external_id": job.get("id", ""),
            "name": job.get("name") or "job",
            "status": status,
            "conclusion": cci_status,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "metadata": {
                "job_number": job.get("number"),
                "event_type": "job",
            },
        }
