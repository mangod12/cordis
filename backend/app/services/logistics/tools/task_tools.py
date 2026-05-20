"""
Task manipulation tools — used by agents to create subtasks and update task state.
These tools operate directly on the database.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.services.logistics.tools.registry import tool_registry

logger = logging.getLogger(__name__)


async def create_subtask(
    parent_task_id: str,
    title: str,
    description: str,
    priority: str = "medium",
) -> dict[str, Any]:
    """
    Create a subtask under a parent task.

    Args:
        parent_task_id: UUID of the parent task
        title: Short title for the subtask
        description: Detailed description of the subtask
        priority: Priority level — critical, high, medium, or low

    Returns:
        dict with created subtask 'id' and metadata
    """
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository

    logger.info(f"[create_subtask] parent={parent_task_id}, title={title!r}")

    try:
        parent_id = uuid.UUID(parent_task_id)
    except ValueError:
        return {"error": f"Invalid parent_task_id UUID: {parent_task_id}"}

    if priority not in ("critical", "high", "medium", "low"):
        priority = "medium"

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        subtask = await repo.create(
            title=title,
            description=description,
            priority=priority,
            parent_task_id=parent_id,
        )
        return {
            "id": str(subtask.id),
            "title": subtask.title,
            "description": subtask.description,
            "priority": subtask.priority,
            "status": subtask.status.value,
            "parent_task_id": str(subtask.parent_task_id),
        }


async def update_task_status(
    task_id: str,
    status: str,
) -> dict[str, Any]:
    """
    Update the status of a task.

    Args:
        task_id: UUID of the task to update
        status: New status — pending, planning, executing, completed, or failed

    Returns:
        dict confirming the update
    """
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository
    from app.models.logistics import TaskStatus

    logger.info(f"[update_task_status] task={task_id}, status={status!r}")

    valid_statuses = {s.value for s in TaskStatus}
    if status not in valid_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of: {sorted(valid_statuses)}"}

    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        return {"error": f"Invalid task_id UUID: {task_id}"}

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        await repo.update_status(tid, TaskStatus(status))
        return {"task_id": task_id, "status": status, "updated": True}


async def estimate_effort(
    task_description: str,
    complexity: str = "medium",
) -> dict[str, Any]:
    """
    Estimate effort and timeline for a task based on description and complexity.

    Args:
        task_description: Description of the task to estimate
        complexity: Complexity level — low, medium, high, or critical

    Returns:
        dict with estimated duration, resource requirements, and confidence
    """
    logger.info(f"[estimate_effort] complexity={complexity!r}")

    complexity_map = {
        "low": {"hours": 4, "days": 0.5, "team_size": 1, "confidence": 0.90},
        "medium": {"hours": 16, "days": 2, "team_size": 2, "confidence": 0.80},
        "high": {"hours": 40, "days": 5, "team_size": 3, "confidence": 0.70},
        "critical": {"hours": 80, "days": 10, "team_size": 5, "confidence": 0.60},
    }

    estimate = complexity_map.get(complexity, complexity_map["medium"])

    return {
        "task_description": task_description[:200],
        "complexity": complexity,
        "estimated_hours": estimate["hours"],
        "estimated_days": estimate["days"],
        "recommended_team_size": estimate["team_size"],
        "confidence": estimate["confidence"],
        "notes": f"Estimate generated for {complexity} complexity task. Adjust based on team expertise and available resources.",
    }


# ── Register tools ───────────────────────────────────────

tool_registry.register(
    name="create_subtask",
    description="Create a subtask under a parent task. Use this to break a complex task into smaller, manageable pieces.",
    parameters={
        "type": "object",
        "properties": {
            "parent_task_id": {
                "type": "string",
                "description": "UUID of the parent task",
            },
            "title": {
                "type": "string",
                "description": "Short, descriptive title for the subtask",
            },
            "description": {
                "type": "string",
                "description": "Detailed description of what needs to be done in this subtask",
            },
            "priority": {
                "type": "string",
                "description": "Priority level: critical, high, medium, or low",
            },
        },
        "required": ["parent_task_id", "title", "description"],
    },
    handler=create_subtask,
)

tool_registry.register(
    name="update_task_status",
    description="Update the status of a task. Use this to mark tasks as planning, executing, completed, or failed.",
    parameters={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "UUID of the task to update",
            },
            "status": {
                "type": "string",
                "description": "New status: pending, resource_assessment, planning, executing, replanning, completed, or failed",
            },
        },
        "required": ["task_id", "status"],
    },
    handler=update_task_status,
)

tool_registry.register(
    name="estimate_effort",
    description="Estimate effort, duration, and resource requirements for a task based on its description and complexity.",
    parameters={
        "type": "object",
        "properties": {
            "task_description": {
                "type": "string",
                "description": "Description of the task to estimate",
            },
            "complexity": {
                "type": "string",
                "description": "Complexity level: low, medium, high, or critical",
            },
        },
        "required": ["task_description"],
    },
    handler=estimate_effort,
)
