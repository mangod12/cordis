"""
Calendar tool — schedules deliveries and supply chain milestones.
Used by the Execution agent to create scheduled entries in the database.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from app.services.logistics.tools.registry import tool_registry

logger = logging.getLogger(__name__)


async def schedule_delivery(
    task_id: str,
    item: str,
    quantity: int,
    scheduled_date: str,
    destination: str,
    priority: str = "medium",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """
    Schedule a delivery as a memory entry with calendar metadata.

    Args:
        task_id: UUID of the parent task
        item: Item or resource being delivered
        quantity: Number of units to deliver
        scheduled_date: ISO date string (YYYY-MM-DD) for the delivery
        destination: Delivery destination / facility
        priority: Priority level — critical, high, medium, or low
        notes: Optional additional notes

    Returns:
        dict with the scheduled delivery details
    """
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import MemoryRepository

    logger.info(f"[schedule_delivery] item={item!r}, qty={quantity}, date={scheduled_date}")

    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        return {"error": f"Invalid task_id UUID: {task_id}"}

    if priority not in ("critical", "high", "medium", "low"):
        priority = "medium"

    try:
        datetime.strptime(scheduled_date, "%Y-%m-%d")
    except ValueError:
        return {"error": f"Invalid date format: {scheduled_date}. Use YYYY-MM-DD."}

    delivery_id = str(uuid.uuid4())[:8]

    async with async_session_factory() as session:
        repo = MemoryRepository(session)
        await repo.save(
            content=f"Scheduled delivery [{delivery_id}]: {quantity}x {item} to {destination} on {scheduled_date}",
            entry_type="plan",
            task_id=tid,
            metadata={
                "type": "delivery_schedule",
                "delivery_id": delivery_id,
                "item": item,
                "quantity": quantity,
                "scheduled_date": scheduled_date,
                "destination": destination,
                "priority": priority,
                "notes": notes,
            },
        )

    return {
        "delivery_id": delivery_id,
        "item": item,
        "quantity": quantity,
        "scheduled_date": scheduled_date,
        "destination": destination,
        "priority": priority,
        "notes": notes,
        "status": "scheduled",
    }


# ── Register tool ────────────────────────────────────────

tool_registry.register(
    name="schedule_delivery",
    description="Schedule a supply chain delivery. Creates a calendar entry for an item delivery to a specific destination on a given date.",
    parameters={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "UUID of the parent task",
            },
            "item": {
                "type": "string",
                "description": "Item or resource being delivered",
            },
            "quantity": {
                "type": "integer",
                "description": "Number of units to deliver",
            },
            "scheduled_date": {
                "type": "string",
                "description": "Delivery date in YYYY-MM-DD format",
            },
            "destination": {
                "type": "string",
                "description": "Delivery destination or facility name",
            },
            "priority": {
                "type": "string",
                "description": "Priority level: critical, high, medium, or low",
            },
            "notes": {
                "type": "string",
                "description": "Optional additional notes about the delivery",
            },
        },
        "required": ["task_id", "item", "quantity", "scheduled_date", "destination"],
    },
    handler=schedule_delivery,
)
