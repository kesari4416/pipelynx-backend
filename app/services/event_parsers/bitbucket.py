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
        # Pipeline events have a `pipeline` key; raw pushes have `push.changes`.
        if "pipeline" in payload and "repository" in payload:
            return True
        if event_type == "repo:push" and "push" in payload:
            return True
        return False

    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Raw push (no pipeline ran) — capture as a synthetic run
        if event_type == "repo:push" and "push" in payload and "pipeline" not in payload:
            return self._parse_push(payload)
        return self._parse_pipeline_event(payload)

    def _parse_pipeline_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    def _parse_push(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Bitbucket `repo:push` event — one run per push."""
        push = payload.get("push") or {}
        changes = push.get("changes") or []
        if not changes:
            return None
        # Use the most recent change (last entry)
        change = changes[-1]
        new = change.get("new") or {}
        # Branch deletion → "new" is null
        if not new:
            return None
        target = new.get("target") or {}
        branch = new.get("name")
        commit_sha = target.get("hash")
        if not commit_sha:
            return None

        repository = payload.get("repository") or {}
        actor = payload.get("actor") or {}
        commit_author = (target.get("author") or {}).get("user") or {}

        started_at = self.parse_iso_datetime(target.get("date"))
        return {
            "source": self.source,
            "external_id": f"push:{commit_sha}",
            "external_url": (target.get("links") or {}).get("html", {}).get("href"),
            "name": f"push to {branch}" if branch else "push",
            "repository": repository.get("full_name"),
            "branch": branch,
            "commit_sha": commit_sha,
            "commit_message": target.get("message"),
            "author": (
                commit_author.get("nickname")
                or commit_author.get("display_name")
                or actor.get("nickname")
                or actor.get("display_name")
            ),
            "trigger": "push",
            "status": "success",
            "conclusion": "success",
            "started_at": started_at,
            "completed_at": started_at,
            "duration_seconds": 0,
            "metadata": {
                "ref_type": new.get("type"),
                "forced": change.get("forced", False),
                "commits_count": len(change.get("commits") or []),
                "event_type": "push",
            },
        }
