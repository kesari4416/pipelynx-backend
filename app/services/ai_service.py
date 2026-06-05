"""
AI Service - LLM-powered failure analysis, log summarization, and digest generation.
Uses Emergent LLM Key for OpenAI GPT-5.4 access.
"""
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase
from emergentintegrations.llm.chat import LlmChat, UserMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

# System prompts for different AI tasks
LOG_SUMMARY_SYSTEM = """You are a senior DevOps engineer analyzing CI/CD pipeline failures.

Given pipeline run data (status, error messages, metadata), provide:
1. A ONE-SENTENCE root cause hypothesis
2. A short technical summary (2-3 sentences max)
3. Concrete next-step recommendations

Be precise, technical, and actionable. NO fluff. NO disclaimers. Return JSON only.

Output schema:
{
  "root_cause": "string (one sentence)",
  "summary": "string (2-3 sentences)",
  "recommendations": ["string", "string", ...]
}"""

PATTERN_ANALYSIS_SYSTEM = """You are a senior SRE analyzing patterns across multiple pipeline failures.

Given a list of recent failures with metadata, identify:
1. Common patterns or correlations
2. Probable systemic issues (vs one-off failures)
3. Risk areas requiring immediate attention

Be precise. Return JSON only.

Output schema:
{
  "patterns": ["pattern 1", "pattern 2", ...],
  "systemic_issues": ["issue 1", ...],
  "priority_actions": ["action 1", ...]
}"""

DIGEST_SYSTEM = """You are an engineering manager preparing a weekly pipeline health digest.

Given DORA metrics and recent activity stats, write a concise executive summary in plain text (no markdown).

Cover:
- Overall health (1 sentence)
- Key wins this period
- Top concerns
- One specific recommendation for next week

Maximum 4 short paragraphs. Tone: confident, direct, no buzzwords."""


class AIService:
    """Service for AI-powered pipeline analysis"""
    
    @staticmethod
    def _create_chat(session_id: str, system_message: str) -> LlmChat:
        """Helper: build configured LlmChat instance"""
        return LlmChat(
            api_key=settings.EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message,
        ).with_model("openai", "gpt-4o-mini")
    
    @staticmethod
    async def _send(chat: LlmChat, prompt: str) -> str:
        """Helper: send a non-streamed message and accumulate the response"""
        from emergentintegrations.llm.chat import TextDelta, StreamDone
        
        chunks: List[str] = []
        async for event in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(event, TextDelta):
                chunks.append(event.content)
            elif isinstance(event, StreamDone):
                break
        return "".join(chunks).strip()
    
    @staticmethod
    def _parse_json_safe(text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON safely, stripping markdown code fences if present"""
        cleaned = text.strip()
        # Strip ```json ... ``` fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from LLM response: {cleaned[:200]}")
            return None
    
    @classmethod
    async def summarize_run_failure(cls, run: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single failed pipeline run and produce root cause + recommendations.
        Returns dict with root_cause, summary, recommendations.
        """
        if not settings.EMERGENT_LLM_KEY:
            return {
                "root_cause": "AI analysis unavailable",
                "summary": "EMERGENT_LLM_KEY not configured.",
                "recommendations": [],
            }
        
        # Build context — limit raw_payload to avoid token blowup
        context = {
            "source": run.get("source"),
            "name": run.get("name"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "repository": run.get("repository"),
            "branch": run.get("branch"),
            "commit_sha": (run.get("commit_sha") or "")[:12],
            "commit_message": (run.get("commit_message") or "")[:200],
            "duration_seconds": run.get("duration_seconds"),
            "error_message": (run.get("error_message") or "")[:1000],
            "trigger": run.get("trigger"),
        }
        
        session_id = f"failure-analysis-{run.get('id', uuid.uuid4())}"
        chat = cls._create_chat(session_id, LOG_SUMMARY_SYSTEM)
        prompt = f"Analyze this pipeline run failure and return JSON:\n\n{json.dumps(context, indent=2, default=str)}"
        
        try:
            response = await cls._send(chat, prompt)
            parsed = cls._parse_json_safe(response)
            if parsed:
                return {
                    "root_cause": parsed.get("root_cause", ""),
                    "summary": parsed.get("summary", ""),
                    "recommendations": parsed.get("recommendations", []),
                }
            # Fallback: use raw text
            return {
                "root_cause": "Analysis available",
                "summary": response[:300],
                "recommendations": [],
            }
        except Exception as e:
            logger.error(f"AI summarization failed: {e}", exc_info=True)
            return {
                "root_cause": "AI analysis failed",
                "summary": str(e)[:200],
                "recommendations": [],
            }
    
    @classmethod
    async def analyze_failure_patterns(
        cls,
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Analyze patterns across recent failures for an organization.
        """
        if not settings.EMERGENT_LLM_KEY:
            return {"patterns": [], "systemic_issues": [], "priority_actions": []}
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        failures = await db.pipeline_runs.find(
            {
                "organization_id": organization_id,
                "status": "failure",
                "created_at": {"$gte": since},
            },
            {"_id": 0, "raw_payload": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        if not failures:
            return {
                "patterns": [],
                "systemic_issues": [],
                "priority_actions": ["No failures in this period — keep up the good work!"],
            }
        
        # Compact failure summaries to keep token usage manageable
        compact = [
            {
                "source": f.get("source"),
                "name": f.get("name"),
                "repository": f.get("repository"),
                "branch": f.get("branch"),
                "error": (f.get("error_message") or f.get("conclusion") or "")[:200],
                "duration": f.get("duration_seconds"),
                "when": f.get("created_at"),
            }
            for f in failures
        ]
        
        session_id = f"pattern-analysis-{organization_id}-{datetime.now(timezone.utc).date()}"
        chat = cls._create_chat(session_id, PATTERN_ANALYSIS_SYSTEM)
        prompt = f"Analyze these {len(compact)} pipeline failures from the last {days} days:\n\n{json.dumps(compact, default=str)}"
        
        try:
            response = await cls._send(chat, prompt)
            parsed = cls._parse_json_safe(response)
            if parsed:
                return {
                    "patterns": parsed.get("patterns", []),
                    "systemic_issues": parsed.get("systemic_issues", []),
                    "priority_actions": parsed.get("priority_actions", []),
                    "analyzed_failures": len(compact),
                    "period_days": days,
                }
            return {"patterns": [], "systemic_issues": [response[:300]], "priority_actions": []}
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}", exc_info=True)
            return {"patterns": [], "systemic_issues": [str(e)[:200]], "priority_actions": []}
    
    @classmethod
    async def generate_weekly_digest(
        cls,
        db: AsyncIOMotorDatabase,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Generate a weekly digest summary from metrics"""
        if not settings.EMERGENT_LLM_KEY:
            return {"digest": "AI digest unavailable (EMERGENT_LLM_KEY not configured).", "generated_at": datetime.now(timezone.utc).isoformat()}
        
        from app.services.metrics_service import MetricsService
        
        # Gather data
        summary = await MetricsService.organization_summary(db, organization_id, days=7)
        dora = await MetricsService.dora_metrics(db, organization_id, days=7)
        top_failing = await MetricsService.top_failing_pipelines(db, organization_id, days=7, limit=5)
        
        context = {
            "summary": summary,
            "dora_metrics": dora,
            "top_failing_pipelines": top_failing,
        }
        
        session_id = f"digest-{organization_id}-{datetime.now(timezone.utc).date()}"
        chat = cls._create_chat(session_id, DIGEST_SYSTEM)
        prompt = f"Generate a weekly digest from this data:\n\n{json.dumps(context, default=str, indent=2)}"
        
        try:
            response = await cls._send(chat, prompt)
            return {
                "digest": response,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stats": {
                    "total_runs": summary.get("total_runs", 0),
                    "success_rate": summary.get("success_rate", 0),
                    "deployment_frequency": dora.get("deployment_frequency_per_day", 0),
                },
            }
        except Exception as e:
            logger.error(f"Digest generation failed: {e}", exc_info=True)
            return {"digest": f"Failed to generate digest: {str(e)[:200]}", "generated_at": datetime.now(timezone.utc).isoformat()}
    
    @classmethod
    async def detect_anomalies(
        cls,
        db: AsyncIOMotorDatabase,
        organization_id: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Statistical anomaly detection (no LLM required).
        Flags runs whose duration is significantly higher than the average for their pipeline.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Group by pipeline + compute avg/stddev
        pipeline_stats = await db.pipeline_runs.aggregate([
            {"$match": {
                "organization_id": organization_id,
                "created_at": {"$gte": since},
                "status": "success",
                "duration_seconds": {"$ne": None, "$gt": 0},
            }},
            {"$group": {
                "_id": {"pipeline": "$pipeline_id", "name": "$name"},
                "avg_duration": {"$avg": "$duration_seconds"},
                "max_duration": {"$max": "$duration_seconds"},
                "count": {"$sum": 1},
                "stddev": {"$stdDevPop": "$duration_seconds"},
            }},
            {"$match": {"count": {"$gte": 3}}},  # Need at least 3 runs for meaningful stats
        ]).to_list(1000)
        
        # Build pipeline lookup
        stats_lookup = {(s["_id"].get("pipeline"), s["_id"].get("name")): s for s in pipeline_stats}
        
        # Find runs with duration > avg + 2*stddev
        recent_runs = await db.pipeline_runs.find(
            {
                "organization_id": organization_id,
                "created_at": {"$gte": since},
                "duration_seconds": {"$ne": None, "$gt": 0},
            },
            {"_id": 0, "raw_payload": 0}
        ).sort("created_at", -1).limit(500).to_list(500)
        
        anomalies = []
        for run in recent_runs:
            key = (run.get("pipeline_id"), run.get("name"))
            stats = stats_lookup.get(key)
            if not stats or not stats.get("stddev"):
                continue
            threshold = stats["avg_duration"] + 2 * stats["stddev"]
            duration = run.get("duration_seconds", 0)
            if duration > threshold and duration > stats["avg_duration"] * 1.5:
                anomalies.append({
                    "run_id": run["id"],
                    "name": run["name"],
                    "source": run["source"],
                    "repository": run.get("repository"),
                    "duration_seconds": duration,
                    "expected_duration_seconds": round(stats["avg_duration"], 2),
                    "deviation_factor": round(duration / stats["avg_duration"], 2),
                    "created_at": run["created_at"],
                })
        
        # Sort by deviation, return top 20
        anomalies.sort(key=lambda x: x["deviation_factor"], reverse=True)
        return anomalies[:20]
