"""Bitbucket Pipelines event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class BitbucketEventParser(BaseEventParser):
    """Parser for Bitbucket Pipelines events"""
    
    source = "bitbucket"
    
    # Bitbucket state.result.name → normalized status
    RESULT_MAP = {
        "SUCCESSFUL": "success",
        "FAILED": "failure",
        "ERROR": "failure",
        "STOPPED": "cancelled",
        "EXPIRED": "failure",
    }
    
    # Bitbucket state.name → normalized status (for in-progress states)
    STATE_MAP = {
        "PENDING": "queued",
        "IN_PROGRESS": "running",
        "RUNNING": "running",
        "PAUSED": "queued",
        "HALTED": "cancelled",
        "COMPLETED": "success",  # Will be refined by result
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        # Bitbucket uses X-Event-Key header (e.g., "repo:push", "pullrequest:created")
        # Pipeline events have 'pipeline' key in payload
        if event_type and event_type.startswith("repo:") and "pipeline" in payload:
            return True
        return "pipeline" in payload and "repository" in payload
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pipeline = payload.get("pipeline", {})
        repository = payload.get("repository", {})
        if not pipeline:
            return None
        
        state = pipeline.get("state", {})
        state_name = state.get("name", "")
        result = state.get("result", {})
        result_name = result.get("name", "")
        
        # Determine status: result takes precedence if present
        if result_name:
            status = self.RESULT_MAP.get(result_name, "failure")
        else:
            status = self.STATE_MAP.get(state_name, "running")
        
        started_at = self.parse_iso_datetime(pipeline.get("created_on"))
        completed_at = self.parse_iso_datetime(pipeline.get("completed_on"))
        
        target = pipeline.get("target", {})
        commit = target.get("commit", {})
        ref = target.get("ref_name") or target.get("branch", {}).get("name")
        
        trigger_obj = pipeline.get("trigger", {})
        creator = pipeline.get("creator", {})
        
        return {
            "source": self.source,
            "external_id": pipeline.get("uuid") or str(pipeline.get("build_number", "")),
            "name": f"pipeline-{pipeline.get('build_number', '')}",
            "repository": repository.get("full_name"),
            "branch": ref,
            "commit_sha": commit.get("hash"),
            "commit_message": commit.get("message"),
            "author": creator.get("display_name") or creator.get("nickname"),
            "trigger": trigger_obj.get("name") or trigger_obj.get("type"),
            "status": status,
            "conclusion": result_name or state_name,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": pipeline.get("duration_in_seconds") or self.calculate_duration(started_at, completed_at),
            "metadata": {
                "build_number": pipeline.get("build_number"),
                "event_type": "pipeline",
            },
        }
