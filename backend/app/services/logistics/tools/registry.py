"""
Tool registry — central dispatch for all agent tools.
Each tool is a Python callable with a schema that maps to a Gemini function declaration.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Describes a single tool available to agents."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Awaitable[dict[str, Any]]],
    ):
        self.name = name
        self.description = description
        self.parameters = parameters  # JSON Schema format
        self.handler = handler

    def to_gemini_declaration(self) -> dict[str, Any]:
        """Convert to the dict format expected by GeminiClient.generate_with_tools()."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Central registry for all tools. Agents select from these."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Awaitable[dict[str, Any]]],
    ) -> None:
        if name in self._tools:
            logger.warning(f"Tool '{name}' is being re-registered.")
        self._tools[name] = ToolDefinition(name, description, parameters, handler)
        logger.info(f"Registered tool: {name}")

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def get_declarations(self, tool_names: list[str]) -> list[dict[str, Any]]:
        """Get Gemini function declarations for a subset of tools by name."""
        declarations = []
        for n in tool_names:
            tool = self._tools.get(n)
            if tool:
                declarations.append(tool.to_gemini_declaration())
        return declarations

    async def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a tool call by name."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = await tool.handler(**args)
            return result
        except Exception as e:
            logger.exception(f"Tool '{name}' failed: {e}")
            return {"error": str(e)}

    @property
    def all_names(self) -> list[str]:
        return list(self._tools.keys())


# Global singleton
tool_registry = ToolRegistry()
