"""initial schema

Revision ID: 20260505_0001
Revises:
Create Date: 2026-05-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "lessons",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("teacher_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column(
            "source_type",
            sa.Enum("url", "file", "text", name="sourcetype"),
            nullable=True,
        ),
        sa.Column("source_content", sa.Text(), nullable=True),
        sa.Column("cluster_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), nullable=False),
        sa.Column(
            "assignment_type",
            sa.Enum("test", "battle", "analysis", "cards", "retelling", name="assignmenttype"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "finished", "archived", name="assignmentstatus"),
            nullable=True,
        ),
        sa.Column("questions_data", sa.JSON(), nullable=True),
        sa.Column("settings_data", sa.JSON(), nullable=True),
        sa.Column("session_token", sa.String(length=255), nullable=True),
        sa.Column("session_expires_at", sa.DateTime(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=True),
        sa.Column("timer_seconds", sa.Integer(), nullable=True),
        sa.Column("show_results", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
    )

    op.create_table(
        "student_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("student_name", sa.String(length=255), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("progress_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "student_responses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("student_session_id", sa.String(length=36), nullable=False),
        sa.Column("question_index", sa.String(length=50), nullable=True),
        sa.Column("question_difficulty", sa.String(length=10), nullable=True),
        sa.Column("answer_data", sa.JSON(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("teacher_grade", sa.String(length=20), nullable=True),
        sa.Column("score", sa.String(length=10), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"]),
        sa.ForeignKeyConstraint(["student_session_id"], ["student_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("student_responses")
    op.drop_table("student_sessions")
    op.drop_table("assignments")
    op.drop_table("lessons")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS assignmentstatus")
    op.execute("DROP TYPE IF EXISTS assignmenttype")
    op.execute("DROP TYPE IF EXISTS sourcetype")
