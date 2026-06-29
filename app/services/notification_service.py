"""
Notification Service - Multi-channel alerting via Slack, Email, Webhooks.
"""
import logging
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Any, List
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
    """Send alerts via SMTP. Uses Gmail/SendGrid/Resend/SES — anything that speaks SMTP."""

    STATUS_COLORS = {
        "failure": "#EF4444",
        "success": "#10B981",
        "running": "#3B82F6",
        "cancelled": "#A1A1AA",
        "queued": "#F59E0B",
    }

    @classmethod
    def _build_subject(cls, alert: Dict[str, Any]) -> str:
        run = alert.get("run", {})
        status = (run.get("status") or "event").upper()
        emoji = {"FAILURE": "🚨", "SUCCESS": "✅", "RUNNING": "🔄"}.get(status, "🔔")
        name = run.get("name") or "pipeline"
        return f"{emoji} [Pipelynx] {status}: {name}"

    @classmethod
    def _build_text_body(cls, alert: Dict[str, Any]) -> str:
        run = alert.get("run", {})
        lines = [
            f"Pipeline: {run.get('name', '—')}",
            f"Status: {(run.get('status') or '—').upper()}",
            f"Repository: {run.get('repository', '—')}",
            f"Branch: {run.get('branch', '—')}",
            f"Source: {(run.get('source') or '—').upper()}",
            f"Duration: {run.get('duration_seconds', 0)}s",
            "",
            f"Triggered by rule: {alert.get('rule_name', '—')}",
            f"Triggered at: {alert.get('triggered_at', '—')}",
            "",
            f"View run: {run.get('external_url', '—')}",
        ]
        if run.get("error_message"):
            lines.extend(["", "Error message:", run["error_message"][:2000]])
        lines.extend(["", "—", "Pipelynx · CI/CD Monitoring & Analytics", "https://pipelynx.io"])
        return "\n".join(lines)

    @classmethod
    def _build_html_body(cls, alert: Dict[str, Any]) -> str:
        run = alert.get("run", {})
        status = (run.get("status") or "event").lower()
        color = cls.STATUS_COLORS.get(status, "#6B7280")
        status_label = status.upper()
        name = run.get("name") or "Pipeline run"
        repo = run.get("repository") or "—"
        branch = run.get("branch") or "—"
        source = (run.get("source") or "—").upper()
        duration = run.get("duration_seconds", 0)
        external_url = run.get("external_url") or "#"
        error_block = ""
        if run.get("error_message"):
            err_safe = (run["error_message"][:2000]).replace("<", "&lt;").replace(">", "&gt;")
            error_block = f"""
            <div style="margin-top:20px;padding:16px;border-left:3px solid {color};background:#FEF2F2;border-radius:6px;">
              <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#991B1B;font-weight:600;margin-bottom:8px;">Error message</div>
              <pre style="margin:0;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:#7F1D1D;white-space:pre-wrap;word-break:break-word;">{err_safe}</pre>
            </div>
            """

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Pipelynx Alert</title></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#0F172A;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#FFFFFF;border-radius:14px;box-shadow:0 10px 30px rgba(15,23,42,0.06);overflow:hidden;">
        <tr><td style="padding:20px 28px;background:linear-gradient(135deg,#6366F1,#8B5CF6);color:#FFFFFF;">
          <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;opacity:0.9;">Pipelynx · Alert</div>
          <div style="font-size:18px;font-weight:600;margin-top:4px;">{alert.get('rule_name', 'Alert triggered')}</div>
        </td></tr>
        <tr><td style="padding:28px;">
          <div style="display:inline-block;padding:6px 12px;border-radius:999px;background:{color}1A;color:{color};font-weight:600;font-size:12px;letter-spacing:0.08em;text-transform:uppercase;">{status_label}</div>
          <h1 style="font-size:22px;margin:14px 0 6px 0;color:#0F172A;">{name}</h1>
          <div style="font-size:13px;color:#64748B;">{repo} · <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;">{branch}</span></div>

          <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:22px;border:1px solid #E2E8F0;border-radius:10px;overflow:hidden;">
            <tr style="background:#F8FAFC;">
              <td style="padding:10px 14px;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:#64748B;width:35%;">Source</td>
              <td style="padding:10px 14px;font-size:13px;color:#0F172A;">{source}</td>
            </tr>
            <tr><td style="padding:10px 14px;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:#64748B;border-top:1px solid #E2E8F0;">Duration</td>
                <td style="padding:10px 14px;font-size:13px;color:#0F172A;border-top:1px solid #E2E8F0;">{duration}s</td></tr>
            <tr style="background:#F8FAFC;"><td style="padding:10px 14px;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:#64748B;border-top:1px solid #E2E8F0;">Triggered</td>
                <td style="padding:10px 14px;font-size:13px;color:#0F172A;border-top:1px solid #E2E8F0;">{alert.get('triggered_at', '—')}</td></tr>
          </table>

          {error_block}

          <div style="margin-top:24px;">
            <a href="{external_url}" style="display:inline-block;padding:12px 22px;background:#0F172A;color:#FFFFFF;border-radius:10px;font-weight:600;font-size:13px;text-decoration:none;">View pipeline run →</a>
          </div>
        </td></tr>
        <tr><td style="padding:18px 28px;background:#F8FAFC;border-top:1px solid #E2E8F0;font-size:11px;color:#94A3B8;text-align:center;">
          You're receiving this because you configured a Pipelynx alert rule.<br/>
          <a href="https://pipelynx.io" style="color:#6366F1;text-decoration:none;">pipelynx.io</a> · CI/CD Monitoring &amp; Analytics
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    @classmethod
    def _send_sync(cls, recipients: List[str], subject: str, text_body: str, html_body: str) -> None:
        """Blocking SMTP send (run inside asyncio.to_thread)."""
        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        from_name = settings.SMTP_FROM_NAME or "Pipelynx"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((from_name, from_email))
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls(context=context)
                server.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(from_email, recipients, msg.as_string())

    @classmethod
    async def send(cls, recipients: List[str], alert: Dict[str, Any]) -> bool:
        """Send email alert via SMTP. Returns True on success, False on failure."""
        if not recipients:
            logger.warning("EmailNotifier.send called with empty recipients")
            return False

        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(
                "[EMAIL ALERT] SMTP not configured — would have sent to %s",
                recipients,
            )
            return False

        subject = cls._build_subject(alert)
        text_body = cls._build_text_body(alert)
        html_body = cls._build_html_body(alert)

        try:
            await asyncio.to_thread(cls._send_sync, recipients, subject, text_body, html_body)
            logger.info(
                "[EMAIL ALERT SENT] to=%s subject=%s rule=%s",
                recipients, subject, alert.get("rule_name"),
            )
            return True
        except Exception as e:
            logger.error("Email send failed via SMTP %s: %s", settings.SMTP_HOST, e)
            return False


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
