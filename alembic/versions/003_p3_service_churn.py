"""p3: add ServiceContractChurn for SERVICIOS churn analysis + contract churn fields

Revision ID: 003
Revises: 002
Create Date: 2026-07-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SERVICE_CHURN_VALUES = (
    "SCOPE_CREEP", "BUDGET_OVERRUN", "TIMELINE_ISSUES",
    "QUALITY_CONCERNS", "RELATIONSHIP_BREAKDOWN", "STRATEGIC_SHIFT", "OTHER",
)


def upgrade() -> None:
    # Create enum type idempotently
    op.execute(
        """DO $$ BEGIN
            CREATE TYPE servicechurncategory AS ENUM (%s);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;""" % ", ".join("'%s'" % v for v in SERVICE_CHURN_VALUES)
    )

    # Add churn fields to commercial_contracts
    op.add_column("commercial_contracts", sa.Column("churned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("commercial_contracts", sa.Column("churn_reason", sa.Text(), nullable=True))

    # commercial_service_churn — use sa.Text() for category column to avoid
    # SQLAlchemy's before_create event re-creating the enum type that already
    # exists. The DB enum type is created above; the column stores the text
    # values which the application-layer Enum validates.
    op.create_table(
        "commercial_service_churn",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("commercial_contracts.id"), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("revenue_lost", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_completion_pct", sa.Integer(), nullable=True),
        sa.Column("retention_attempts", sa.JSON(), server_default="[]"),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("analyzed_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("commercial_service_churn")

    op.drop_column("commercial_contracts", "churn_reason")
    op.drop_column("commercial_contracts", "churned_at")

    op.execute("DROP TYPE IF EXISTS servicechurncategory CASCADE;")
