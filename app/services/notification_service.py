"""
Notification Service - Multi-channel alerting via Slack, Email, Webhooks.
"""
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============ Channel adapters ============

class SlackNotifier:
    """Send alerts to Slack via incoming webhook URL"""
    
    @staticmethod
    async def send(webhook_url: str, alert: Dict[str, Any]) -> bool:
        """Post a richly formatted message to Slack"""
        run = alert.get("run", {})
        status_emoji = {
            "failure": ":x:",
            "success": ":white_check_mark:",
            "running": ":hourglass_flowing_sand:",
            "cancelled": ":no_entry:",
            "queued": ":timer_clock:",
        }.get(run.get("status", ""), ":bell:")
        
        color = {
            "failure": "#FF3B30",
            "success": "#2ECC71",
            "running": "#3B82F6",
            "cancelled": "#A1A1AA",
            "queued": "#F59E0B",
        }.get(run.get("status", ""), "#A1A1AA")
        
        payload = {
            "text": f"{status_emoji} Pipeline {run.get('status', 'event')}: {run.get('name', 'unknown')}",
            "attachments": [{
                "color": color,
                "title": f"{run.get('name', 'Pipeline Run')}",
                "title_link": run.get("external_url"),
                "fields": [
                    {"title": "Repository", "value": run.get("repository", "—"), "short": True},
                    {"title": "Branch", "value": run.get("branch", "—"), "short": True},
                    {"title": "Source", "value": run.get("source", "—").upper(), "short": True},
                    {"title": "Duration", "value": f"{run.get('duration_seconds', 0)}s", "short": True},
                ],
                "footer": f"Pipelynx · {alert.get('rule_name', 'Alert')}",
                "ts": int(datetime.now(timezone.utc).timestamp()),
            }],
        }
        
        if run.get("error_message"):
            payload["attachments"][0]["fields"].append({
                "title": "Error",
                "value": run["error_message"][:500],
                "short": False,
            })
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False


class EmailNotifier:
    """Send alerts via SMTP (placeholder — requires SMTP credentials in production)"""
    
    @staticmethod
    async def send(recipients: List[str], alert: Dict[str, Any]) -> bool:
        """Send email alert. Currently logs but doesn't actually send (no SMTP configured)"""
        run = alert.get("run", {})
        subject = f"[Pipelynx] {run.get('status', 'event').upper()}: {run.get('name', 'pipeline')}"
        
        body_lines = [
            f"Pipeline: {run.get('name', '—')}",
            f"Status: {run.get('status', '—').upper()}",
            f"Repository: {run.get('repository', '—')}",
            f"Branch: {run.get('branch', '—')}",
            f"Source: {run.get('source', '—')}",
            f"Duration: {run.get('duration_seconds', 0)}s",
            "",
            f"View run: {run.get('external_url', '—')}",
        ]
        
        if run.get("error_message"):
            body_lines.extend(["", "Error message:", run["error_message"][:1000]])
        
        body = "\n".join(body_lines)
        
        # In production, integrate with SendGrid/Resend/AWS SES.
        # For now, log that we would send the email.
        logger.info(f"[EMAIL ALERT] To: {recipients} | Subject: {subject}")
        logger.info(f"[EMAIL BODY]\n{body}")
        
        # Simulate success
        return True


class GenericWebhookNotifier:
    """Send alert to a generic webhook endpoint (for PagerDuty, Opsgenie, custom systems)"""
    
    @staticmethod
    async def send(webhook_url: str, alert: Dict[str, Any]) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=alert)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


# ============ Alert Rule Engine ============

class AlertEngine:
    """Evaluates alert rules against pipeline runs and triggers notifications"""
    
    @staticmethod
    def _matches_condition(rule: Dict[str, Any], run: Dict[str, Any]) -> bool:
        """Check if a run matches the rule's condition"""
        condition = rule.get("condition", {})
        
        # Status filter (e.g., only fire on failure)
        if "status" in condition:
            allowed = condition["status"]
            if isinstance(allowed, str):
                allowed = [allowed]
            if run.get("status") not in allowed:
                return False
        
        # Source filter
        if "source" in condition:
            allowed_sources = condition["source"]
            if isinstance(allowed_sources, str):
                allowed_sources = [allowed_sources]
            if run.get("source") not in allowed_sources:
                return False
        
        # Branch filter
        if "branch" in condition:
            if run.get("branch") != condition["branch"]:
                return False
        
        # Repository filter
        if "repository" in condition:
            if run.get("repository") != condition["repository"]:
                return False
        
        # Duration threshold (in seconds)
        if "duration_above_seconds" in condition:
            duration = run.get("duration_seconds") or 0
            if duration < condition["duration_above_seconds"]:
                return False
        
        return True
    
    @classmethod
    async def evaluate(
        cls,
        db: AsyncIOMotorDatabase,
        run: Dict[str, Any],
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all active alert rules against a run, fire matching notifications.
        Returns list of triggered alerts (for logging).
        """
        rules = await db.alert_rules.find(
            {"organization_id": organization_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        triggered = []
        for rule in rules:
            if not cls._matches_condition(rule, run):
                continue
            
            alert = {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "run": run,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Dispatch to each configured channel
            channels = rule.get("channels", [])
            channel_configs = rule.get("channel_configs", {})
            
            for channel in channels:
                channel_cfg = channel_configs.get(channel, {})
                success = False
                
                if channel == "slack":
                    webhook_url = channel_cfg.get("webhook_url")
                    if webhook_url:
                        success = await SlackNotifier.send(webhook_url, alert)
                
                elif channel == "email":
                    recipients = channel_cfg.get("recipients", [])
                    if recipients:
                        success = await EmailNotifier.send(recipients, alert)
                
                elif channel == "webhook":
                    webhook_url = channel_cfg.get("url")
                    if webhook_url:
                        success = await GenericWebhookNotifier.send(webhook_url, alert)
                
                logger.info(f"Alert dispatch: rule={rule['name']} channel={channel} success={success}")
            
            # Log to history collection
            await db.alert_history.insert_one({
                **alert,
                "id": f"alert_{run.get('id', 'unknown')}_{rule['id']}_{int(datetime.now(timezone.utc).timestamp())}",
            })
            triggered.append(alert)
        
        return triggered
