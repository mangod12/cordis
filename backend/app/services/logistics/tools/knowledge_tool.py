"""
Knowledge tool — searches the memory store for relevant past context.
Used by the Researcher agent to leverage accumulated system knowledge.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.services.logistics.tools.registry import tool_registry

logger = logging.getLogger(__name__)


async def knowledge_lookup(
    query: str,
    limit: int = 5,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Search the memory store for entries relevant to a query.

    Args:
        query: The search query to match against memory content
        limit: Maximum number of results to return (1-20)
        task_id: Optional UUID string to scope search to a specific task

    Returns:
        dict with 'entries' list and metadata
    """
    from app.core.database import async_session_factory
    from app.services.logistics.repositories import MemoryRepository
    import uuid

    limit = max(1, min(20, limit))
    logger.info(f"[knowledge_lookup] query={query!r}, limit={limit}, task_id={task_id}")

    async with async_session_factory() as session:
        repo = MemoryRepository(session)

        entries = []
        if task_id:
            try:
                tid = uuid.UUID(task_id)
                entries = list(await repo.get_by_task(tid, limit=limit))
            except ValueError:
                pass

        # Always supplement with global search if task-scoped results are thin
        if len(entries) < limit:
            global_entries = await repo.search(query, limit=limit - len(entries))
            seen_ids = {e.id for e in entries}
            entries.extend(e for e in global_entries if e.id not in seen_ids)

        results = [
            {
                "id": str(entry.id),
                "content": entry.content,
                "entry_type": entry.entry_type.value if hasattr(entry.entry_type, "value") else entry.entry_type,
                "task_id": str(entry.task_id) if entry.task_id else None,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]

    return {
        "query": query,
        "entries": results,
        "count": len(results),
    }


# ── Register tool ────────────────────────────────────────

tool_registry.register(
    name="knowledge_lookup",
    description="Search the knowledge memory store for relevant past context, decisions, or facts. Use this to retrieve information gathered in previous steps or tasks.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to match against stored memory entries",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of memory entries to return (1-20, default 5)",
            },
            "task_id": {
                "type": "string",
                "description": "Optional task UUID to scope the search to a specific task's memory",
            },
        },
        "required": ["query"],
    },
    handler=knowledge_lookup,
)
