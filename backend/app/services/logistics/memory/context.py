"""
Memory context manager — persists and retrieves task context from PostgreSQL.
Used by agents to store reasoning, decisions, and discovered facts.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context and memory for agents.
    Wraps MemoryRepository with a clean interface.
    """

    async def save(
        self,
        content: str,
        entry_type: str = "context",
        task_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Persist a memory entry to the database.

        Args:
            content: The text content to store
            entry_type: Type classification — context, resource, decision, plan, blocker
            task_id: Optional UUID to associate with a task
            metadata: Optional JSON metadata dict

        Returns:
            dict with saved entry id
        """
        from app.core.database import async_session_factory
        from app.services.logistics.repositories import MemoryRepository
        from app.models.logistics import MemoryEntryType

        valid_types = {t.value for t in MemoryEntryType}
        if entry_type not in valid_types:
            entry_type = "context"

        async with async_session_factory() as session:
            repo = MemoryRepository(session)
            entry = await repo.save(
                content=content,
                entry_type=entry_type,
                task_id=task_id,
                metadata=metadata,
            )
            logger.debug(f"[memory] saved entry {entry.id} (type={entry_type})")
            return {
                "id": str(entry.id),
                "entry_type": entry_type,
                "task_id": str(task_id) if task_id else None,
            }

    async def retrieve(
        self,
        task_id: uuid.UUID,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Retrieve memory entries for a specific task.

        Args:
            task_id: UUID of the task to retrieve context for
            limit: Maximum number of entries to return

        Returns:
            List of memory entry dicts ordered by recency
        """
        from app.core.database import async_session_factory
        from app.services.logistics.repositories import MemoryRepository

        async with async_session_factory() as session:
            repo = MemoryRepository(session)
            entries = await repo.get_by_task(task_id, limit=limit)
            return [
                {
                    "id": str(e.id),
                    "content": e.content,
                    "entry_type": e.entry_type.value if hasattr(e.entry_type, "value") else e.entry_type,
                    "metadata": e.metadata_,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ]

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Keyword search across all memory entries.

        Args:
            query: Search string (case-insensitive ILIKE match)
            limit: Maximum number of results

        Returns:
            List of matching memory entry dicts
        """
        from app.core.database import async_session_factory
        from app.services.logistics.repositories import MemoryRepository

        async with async_session_factory() as session:
            repo = MemoryRepository(session)
            entries = await repo.search(query, limit=limit)
            return [
                {
                    "id": str(e.id),
                    "content": e.content,
                    "entry_type": e.entry_type.value if hasattr(e.entry_type, "value") else e.entry_type,
                    "task_id": str(e.task_id) if e.task_id else None,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ]

    def format_for_prompt(self, entries: list[dict[str, Any]]) -> str:
        """Format memory entries as a readable string for inclusion in prompts."""
        if not entries:
            return "No prior context available."

        lines = ["=== Prior Context from Memory ==="]
        for e in entries:
            lines.append(f"[{e['entry_type'].upper()}] {e['content']}")
        return "\n".join(lines)


# Module-level singleton
context_manager = ContextManager()
