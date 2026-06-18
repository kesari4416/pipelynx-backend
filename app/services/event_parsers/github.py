"""GitHub Actions event parser"""
from typing import Dict, Any, Optional
from app.services.event_parsers.base import BaseEventParser


class GitHubEventParser(BaseEventParser):
    """Parser for GitHub Actions workflow events"""
    
    source = "github"
    
    # GitHub workflow run conclusion → normalized status mapping
    STATUS_MAP = {
        "success": "success",
        "failure": "failure",
        "cancelled": "cancelled",
        "skipped": "skipped",
        "timed_out": "failure",
        "action_required": "failure",
        "neutral": "success",
        "stale": "cancelled",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        """Handle workflow runs, jobs, check runs, and raw pushes."""
        return event_type in ("workflow_run", "workflow_job", "check_run", "push")
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if event_type == "workflow_run":
            return self._parse_workflow_run(payload)
        if event_type == "workflow_job":
            return self._parse_workflow_job(payload)
        if event_type == "check_run":
            return self._parse_check_run(payload)
        if event_type == "push":
            return self._parse_push(payload)
        return None
    
    def _parse_workflow_run(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse workflow_run event"""
        run = payload.get("workflow_run", {})
        repo = payload.get("repository", {})
        if not run:
            return None
        
        # Initialize with defaults to ensure variable is always defined
        status = "running"
        gh_status = run.get("status", "")  # queued, in_progress, completed
        gh_conclusion = run.get("conclusion")  # success, failure, etc.
        
        if gh_status == "completed" and gh_conclusion:
            status = self.STATUS_MAP.get(gh_conclusion, "failure")
        elif gh_status in ("queued", "requested", "waiting"):
            status = "queued"
        
        started_at = self.parse_iso_datetime(run.get("run_started_at") or run.get("created_at"))
        completed_at = None
        if status not in ("running", "queued"):
            completed_at = self.parse_iso_datetime(run.get("updated_at"))
        
        head_commit = run.get("head_commit") or {}
        actor = run.get("triggering_actor") or run.get("actor") or {}
        
        return {
            "source": self.source,
            "external_id": str(run.get("id", "")),
            "external_url": run.get("html_url"),
            "name": run.get("name") or run.get("display_title") or "workflow",
            "repository": repo.get("full_name"),
            "branch": run.get("head_branch"),
            "commit_sha": run.get("head_sha"),
            "commit_message": head_commit.get("message"),
            "author": actor.get("login"),
            "trigger": run.get("event"),
            "status": status,
            "conclusion": gh_conclusion,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "metadata": {
                "run_number": run.get("run_number"),
                "run_attempt": run.get("run_attempt"),
                "workflow_id": run.get("workflow_id"),
                "event_type": "workflow_run",
            },
        }
    
    def _parse_workflow_job(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse workflow_job event"""
        job = payload.get("workflow_job", {})
        repo = payload.get("repository", {})
        if not job:
            return None
        
        # Initialize with default to ensure status is always defined
        status = "running"
        gh_status = job.get("status", "")
        gh_conclusion = job.get("conclusion")
        
        if gh_status == "completed" and gh_conclusion:
            status = self.STATUS_MAP.get(gh_conclusion, "failure")
        elif gh_status == "queued":
            status = "queued"
        
        started_at = self.parse_iso_datetime(job.get("started_at"))
        completed_at = self.parse_iso_datetime(job.get("completed_at"))
        
        return {
            "source": self.source,
            "external_id": str(job.get("id", "")),
            "external_url": job.get("html_url"),
            "name": job.get("name") or "job",
            "repository": repo.get("full_name"),
            "branch": job.get("head_branch"),
            "commit_sha": job.get("head_sha"),
            "status": status,
            "conclusion": gh_conclusion,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "metadata": {
                "run_id": job.get("run_id"),
                "workflow_name": job.get("workflow_name"),
                "event_type": "workflow_job",
            },
        }
    
    def _parse_check_run(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse check_run event"""
        check = payload.get("check_run", {})
        repo = payload.get("repository", {})
        if not check:
            return None
        
        gh_conclusion = check.get("conclusion") or ""
        status = self.STATUS_MAP.get(gh_conclusion, "running")
        started_at = self.parse_iso_datetime(check.get("started_at"))
        completed_at = self.parse_iso_datetime(check.get("completed_at"))
        
        return {
            "source": self.source,
            "external_id": str(check.get("id", "")),
            "external_url": check.get("html_url"),
            "name": check.get("name") or "check",
            "repository": repo.get("full_name"),
            "commit_sha": check.get("head_sha"),
            "status": status,
            "conclusion": gh_conclusion,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": self.calculate_duration(started_at, completed_at),
            "metadata": {"event_type": "check_run"},
        }

    def _parse_push(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a raw `push` event — one PipelineRun per push that arrives.

        Pushes are not pipelines themselves, but treating them as runs gives a
        complete commit-by-commit timeline of activity, even when the repo has
        no GitHub Actions workflows configured.
        """
        # Ignore branch / tag deletions (head_commit is null)
        if payload.get("deleted"):
            return None
        head_commit = payload.get("head_commit") or {}
        if not head_commit:
            return None

        repo = payload.get("repository", {})
        pusher = payload.get("pusher") or {}
        sender = payload.get("sender") or {}
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref

        started_at = self.parse_iso_datetime(head_commit.get("timestamp"))
        # A push is instantaneous — treat it as a 0-duration "success" entry.
        return {
            "source": self.source,
            "external_id": f"push:{head_commit.get('id', '')}",
            "external_url": payload.get("compare") or head_commit.get("url"),
            "name": f"push to {branch}" if branch else "push",
            "repository": repo.get("full_name"),
            "branch": branch,
            "commit_sha": head_commit.get("id"),
            "commit_message": head_commit.get("message"),
            "author": (
                head_commit.get("author", {}).get("username")
                or head_commit.get("author", {}).get("name")
                or pusher.get("name")
                or sender.get("login")
            ),
            "trigger": "push",
            "status": "success",
            "conclusion": "success",
            "started_at": started_at,
            "completed_at": started_at,
            "duration_seconds": 0,
            "metadata": {
                "ref": ref,
                "commits_count": len(payload.get("commits") or []),
                "forced": payload.get("forced", False),
                "event_type": "push",
            },
        }
