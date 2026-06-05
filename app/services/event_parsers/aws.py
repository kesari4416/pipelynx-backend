"""AWS CodePipeline event parser (via CloudWatch Events / SNS)"""
from typing import Dict, Any, Optional
import json
from app.services.event_parsers.base import BaseEventParser


class AWSEventParser(BaseEventParser):
    """Parser for AWS CodePipeline/CodeBuild events"""
    
    source = "aws"
    
    # AWS state → normalized status
    STATE_MAP = {
        "STARTED": "running",
        "RESUMED": "running",
        "SUCCEEDED": "success",
        "FAILED": "failure",
        "STOPPED": "cancelled",
        "STOPPING": "cancelled",
        "CANCELED": "cancelled",
        "SUPERSEDED": "skipped",
        "IN_PROGRESS": "running",
        "QUEUED": "queued",
    }
    
    def can_parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> bool:
        # AWS CloudWatch events have 'source' = 'aws.codepipeline' or similar
        # SNS messages wrap the event in Message field
        if "Message" in payload:
            try:
                inner = json.loads(payload["Message"]) if isinstance(payload["Message"], str) else payload["Message"]
                return self._is_aws_event(inner)
            except (json.JSONDecodeError, TypeError):
                return False
        return self._is_aws_event(payload)
    
    def _is_aws_event(self, payload: Dict[str, Any]) -> bool:
        source = payload.get("source", "")
        return source.startswith("aws.code") or "detail" in payload
    
    def parse(self, event_type: Optional[str], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Unwrap SNS message if needed
        if "Message" in payload:
            try:
                payload = json.loads(payload["Message"]) if isinstance(payload["Message"], str) else payload["Message"]
            except (json.JSONDecodeError, TypeError):
                return None
        
        detail = payload.get("detail", {})
        if not detail:
            return None
        
        aws_source = payload.get("source", "")
        state = detail.get("state", "")
        status = self.STATE_MAP.get(state, "running")
        
        started_at = self.parse_iso_datetime(payload.get("time"))
        
        # Initialize with defaults to ensure variables are always defined
        name = aws_source or "aws-pipeline"
        external_id = str(payload.get("id", ""))
        external_url = None
        
        # Build name varies by AWS service
        if "codepipeline" in aws_source:
            name = detail.get("pipeline") or "codepipeline"
            external_id = f"{name}-{detail.get('execution-id', '')}"
        elif "codebuild" in aws_source:
            name = detail.get("project-name") or "codebuild"
            external_id = detail.get("build-id", "")
        
        return {
            "source": self.source,
            "external_id": str(external_id),
            "external_url": external_url,
            "name": name,
            "status": status,
            "conclusion": state,
            "started_at": started_at,
            "metadata": {
                "aws_source": aws_source,
                "region": payload.get("region"),
                "account": payload.get("account"),
                "execution_id": detail.get("execution-id"),
                "event_type": "aws-event",
            },
        }
