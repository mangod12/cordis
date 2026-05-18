"""Initial schema — tasks, agent_logs, memory_entries tables."""

from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── task_status enum ─────────────────────────────────
    task_status = postgresql.ENUM(
        "pending", "resource_assessment", "planning",
        "executing", "replanning", "completed", "failed",
        name="task_status",
    )
    task_status.create(op.get_bind(), checkfirst=True)

    # ── memory_entry_type enum ────────────────────────────
    memory_entry_type = postgresql.ENUM(
        "context", "resource", "decision", "plan", "blocker",
        name="memory_entry_type",
    )
    memory_entry_type.create(op.get_bind(), checkfirst=True)

    # ── tasks table ───────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.Enum(
            "pending", "resource_assessment", "planning",
            "executing", "replanning", "completed", "failed",
            name="task_status",
        ), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("result_plan", postgresql.JSONB, nullable=True),
        sa.Column("result_tasks", postgresql.JSONB, nullable=True),
        sa.Column("result_schedule", postgresql.JSONB, nullable=True),
        sa.Column("result_reasoning", postgresql.JSONB, nullable=True),
        sa.Column("parent_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── agent_logs table ──────────────────────────────────
    op.create_table(
        "agent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("input_data", postgresql.JSONB, nullable=True),
        sa.Column("output_data", postgresql.JSONB, nullable=True),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("token_usage", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_logs_task_id", "agent_logs", ["task_id"])

    # ── memory_entries table ──────────────────────────────
    op.create_table(
        "memory_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("entry_type", sa.Enum(
            "context", "resource", "decision", "plan", "blocker",
            name="memory_entry_type",
        ), nullable=False, server_default="context"),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_memory_entries_task_id", "memory_entries", ["task_id"])


def downgrade() -> None:
    op.drop_table("memory_entries")
    op.drop_table("agent_logs")
    op.drop_table("tasks")

    op.execute("DROP TYPE IF EXISTS memory_entry_type")
    op.execute("DROP TYPE IF EXISTS task_status")
