"""ArgoCD event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class ArgoCDEventParser(BaseEventParser):
    """Parser for ArgoCD application sync events"""
    
    source = "argocd"
    
    # ArgoCD operation phase → normalized status
    PHASE_MAP = {
        "Succeeded": "success",
        "Failed": "failure",
        "Error": "failure",
        "Running": "running",
        "Terminating": "cancelled",
        "Pending": "queued",
    }
    
    # ArgoCD sync status → normalized status (fallback)
    SYNC_STATUS_MAP = {
        "Synced": "success",
        "OutOfSync": "failure",
        "Unknown": "running",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        # ArgoCD typically sends application/resource events with metadata.name
        return ("kind" in payload and payload.get("kind") == "Application") or "application" in payload
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Normalize payload structure
        app = payload if payload.get("kind") == "Application" else payload.get("application", payload)
        
        metadata = app.get("metadata", {})
        spec = app.get("spec", {})
        status_obj = app.get("status", {})
        operation_state = status_obj.get("operationState", {})
        sync = status_obj.get("sync", {})
        health = status_obj.get("health", {})
        source = spec.get("source", {})
        
        # Determine status: prefer operation phase, fallback to sync status
        phase = operation_state.get("phase")
        if phase:
            status = self.PHASE_MAP.get(phase, "running")
        else:
            status = self.SYNC_STATUS_MAP.get(sync.get("status", ""), "running")
        
        started_at = self.parse_iso_datetime(operation_state.get("startedAt"))
        completed_at = self.parse_iso_datetime(operation_state.get("finishedAt"))
        
        return {
            "source": self.source,
            "external_id": metadata.get("uid") or metadata.get("name", ""),
            "name": metadata.get("name") or "argocd-sync",
            "repository": source.get("repoURL"),
            "branch": source.get("targetRevision"),
            "commit_sha": sync.get("revision"),
            "status": status,
            "conclusion": phase or sync.get("status"),
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "error_message": operation_state.get("message") if status == "failure" else None,
            "metadata": {
                "app_namespace": metadata.get("namespace"),
                "destination_namespace": spec.get("destination", {}).get("namespace"),
                "destination_server": spec.get("destination", {}).get("server"),
                "health_status": health.get("status"),
                "sync_status": sync.get("status"),
                "event_type": "application",
            },
        }
