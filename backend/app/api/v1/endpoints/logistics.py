"""Logistics API — crisis supply chain coordination endpoints.

Exposes the Cordis logistics multi-agent pipeline (Resource → Plan → Replan → Execute)
as REST endpoints under /api/v1/logistics/.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────


class LogisticsExecuteRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000, description="Crisis scenario description")


class LogisticsExecuteResponse(BaseModel):
    task_id: str
    status: str
    message: str


class LogisticsTaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    result_plan: dict | None = None
    result_tasks: dict | None = None
    result_schedule: dict | None = None
    result_reasoning: dict | None = None
    created_at: str


# ── Endpoints ────────────────────────────────────────────


@router.post("/execute", response_model=LogisticsExecuteResponse, status_code=202)
async def execute_logistics_pipeline(
    request: LogisticsExecuteRequest,
    background_tasks: BackgroundTasks,
):
    """Run the full logistics agent pipeline for a crisis scenario.

    Creates a task and runs Resource → Planning → Replanning → Execution
    agents in the background. Poll GET /api/v1/logistics/tasks/{task_id}
    for results.
    """
    if not settings.LOGISTICS_ENABLED:
        raise HTTPException(status_code=503, detail="Logistics pipeline is disabled")

    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.create(
            title=request.query[:200],
            description=request.query,
            priority="high",
        )
        task_id = task.id

    background_tasks.add_task(_run_pipeline, task_id, request.query)

    return LogisticsExecuteResponse(
        task_id=str(task_id),
        status="pending",
        message="Logistics pipeline started. Poll /api/v1/logistics/tasks/{task_id} for results.",
    )


@router.get("/tasks")
async def list_logistics_tasks(limit: int = 50, offset: int = 0):
    """List logistics tasks with pagination."""
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        tasks = await repo.list_all(limit=limit, offset=offset)
        return {
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tasks
            ],
            "total": len(tasks),
        }


@router.get("/tasks/{task_id}")
async def get_logistics_task(task_id: str):
    """Get a logistics task with full results."""
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import TaskRepository

    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid task_id UUID")

    async with async_session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.get(tid)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority,
            "result_plan": task.result_plan,
            "result_tasks": task.result_tasks,
            "result_schedule": task.result_schedule,
            "result_reasoning": task.result_reasoning,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }


@router.get("/tasks/{task_id}/logs")
async def get_logistics_task_logs(task_id: str):
    """Get agent execution logs for a logistics task."""
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import AgentLogRepository

    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid task_id UUID")

    async with async_session_factory() as session:
        repo = AgentLogRepository(session)
        logs = await repo.list_by_task(tid)
        return [
            {
                "id": str(log.id),
                "agent_name": log.agent_name,
                "action": log.action,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "reasoning": log.reasoning,
                "token_usage": log.token_usage,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]


# ── Background pipeline runner ───────────────────────────


async def _run_pipeline(task_id: uuid.UUID, query: str) -> None:
    """Run the orchestrator agent pipeline in the background."""
    from app.agents.logistics.orchestrator import OrchestratorAgent

    try:
        orchestrator = OrchestratorAgent()
        await asyncio.wait_for(
            orchestrator.run(
                task_id=task_id,
                task_title=query[:200],
                task_description=query,
            ),
            timeout=settings.PIPELINE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(f"[logistics] Pipeline timed out for task {task_id}")
        from app.core.database import async_session_factory
        from app.services.logistics.repositories import TaskRepository
        from app.models.logistics import TaskStatus

        async with async_session_factory() as session:
            repo = TaskRepository(session)
            await repo.update_status(task_id, TaskStatus.FAILED)
    except Exception:
        logger.exception(f"[logistics] Pipeline failed for task {task_id}")
        from app.core.database import async_session_factory
        from app.services.logistics.repositories import TaskRepository
        from app.models.logistics import TaskStatus

        async with async_session_factory() as session:
            repo = TaskRepository(session)
            await repo.update_status(task_id, TaskStatus.FAILED)
