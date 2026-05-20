"""Pipeline connector — bridges Cordis triage output to Cordis logistics input.

Takes a completed EmergencyResponse (transcript, intent, severity, responder)
and generates a structured crisis query for the logistics pipeline.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Severity thresholds for auto-triggering logistics
_AUTO_TRIGGER_SEVERITIES = {"critical", "high"}

# Intent types that benefit from logistics coordination
_LOGISTICS_INTENTS = {"FIRE", "MEDICAL", "ACCIDENT", "GAS_HAZARD"}


def should_trigger_logistics(
    severity: str,
    intent: str,
    auto_dispatch: bool = True,
) -> bool:
    """Determine if emergency triage results warrant logistics coordination.

    Returns True if severity is critical/high AND intent is a logistics-relevant type.
    """
    if not settings.LOGISTICS_ENABLED:
        return False
    if not auto_dispatch:
        return False
    return (
        severity.lower() in _AUTO_TRIGGER_SEVERITIES
        and intent.upper() in _LOGISTICS_INTENTS
    )


def build_crisis_query(
    transcript: str,
    intent: str,
    severity: str,
    emotion: str,
    responder: str,
    caller_id: Optional[str] = None,
) -> str:
    """Convert emergency triage output into a natural language crisis query
    suitable for the logistics orchestrator agent.

    The orchestrator parses crisis keywords, location names, and resource types
    from free text — so we construct a descriptive query.
    """
    severity_label = severity.capitalize()
    intent_label = intent.replace("_", " ").title()

    query = f"{severity_label} {intent_label} emergency reported."

    if transcript:
        # Include relevant excerpt (orchestrator extracts locations/resources from text)
        excerpt = transcript[:500].strip()
        query += f" Caller reports: \"{excerpt}\""

    query += f" Dispatching {responder}. Immediate resource coordination required."

    if severity.lower() == "critical":
        query += " CRITICAL priority — expedite all logistics."

    return query


async def trigger_logistics_pipeline(
    transcript: str,
    intent: str,
    severity: str,
    emotion: str,
    responder: str,
    caller_id: Optional[str] = None,
) -> Optional[str]:
    """Trigger the logistics pipeline from emergency triage results.

    Returns the logistics task_id if triggered, None if skipped.
    """
    if not should_trigger_logistics(severity, intent):
        return None

    query = build_crisis_query(
        transcript=transcript,
        intent=intent,
        severity=severity,
        emotion=emotion,
        responder=responder,
        caller_id=caller_id,
    )

    logger.info(f"[pipeline_connector] Triggering logistics for {intent}/{severity}")

    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.create(
            title=f"Emergency: {intent} ({severity})",
            description=query,
            priority="critical" if severity.lower() == "critical" else "high",
        )
        task_id = task.id

    # Run pipeline in background (don't block emergency response)
    import asyncio
    from app.api.v1.endpoints.logistics import _run_pipeline

    asyncio.create_task(_run_pipeline(task_id, query))

    return str(task_id)
