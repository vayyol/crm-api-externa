"""Add per-user follow-up dismissals

Revision ID: b81d3e2a9c41
Revises: 06c9ce55a619
Create Date: 2026-11-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b81d3e2a9c41"
down_revision: Union[str, Sequence[str], None] = "06c9ce55a619"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "followup_dismissals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("usuario_externo_id", sa.String(length=36), nullable=False),
        sa.Column("followup_key", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("usuario_externo_id", "followup_key", name="uq_followup_user_key"),
    )
    op.create_index("ix_followup_dismissals_usuario_externo_id", "followup_dismissals", ["usuario_externo_id"])


def downgrade() -> None:
    op.drop_index("ix_followup_dismissals_usuario_externo_id", table_name="followup_dismissals")
    op.drop_table("followup_dismissals")
