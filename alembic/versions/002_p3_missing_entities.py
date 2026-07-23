"""p3: add 5 missing entities (Quote, Handoff, ChurnAnalysis, MarketingPlan, CompetitionMatrix)

Revision ID: 002
Revises: 001
Create Date: 2026-07-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums (IF NOT EXISTS for idempotency)
    op.execute("""DO $$ BEGIN CREATE TYPE quotestatus AS ENUM ('DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE handoffstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE churnreasoncategory AS ENUM ('PRICE', 'PRODUCT_FIT', 'SUPPORT', 'PERFORMANCE', 'COMPETITOR', 'OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE marketingplanstatus AS ENUM ('DRAFT', 'ACTIVE', 'COMPLETED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")

    # commercial_quotes
    op.create_table(
        "commercial_quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("commercial_leads.id"), nullable=False),
        sa.Column("quote_number", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("version", sa.String(10), server_default="1.0"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0.00"),
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0.00"),
        sa.Column("discount_percent", sa.Numeric(5, 2), server_default="0.00"),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0.00"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("lines", sa.JSON(), server_default="[]"),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "SENT", "ACCEPTED", "REJECTED", "EXPIRED", name="quotestatus", create_type=False), server_default="DRAFT"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # commercial_handoffs
    op.create_table(
        "commercial_handoffs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("commercial_contracts.id"), nullable=False),
        sa.Column("target_module", sa.String(50), nullable=False),
        sa.Column("project_manager", sa.String(255), nullable=False),
        sa.Column("handoff_notes", sa.Text(), nullable=True),
        sa.Column("checklist", sa.JSON(), server_default="[]"),
        sa.Column("status", sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", name="handoffstatus", create_type=False), server_default="PENDING"),
        sa.Column("signed_by_sales", sa.String(255), nullable=True),
        sa.Column("signed_by_pm", sa.String(255), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # commercial_churn_analysis
    op.create_table(
        "commercial_churn_analysis",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("commercial_subscriptions.id"), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("category", sa.Enum("PRICE", "PRODUCT_FIT", "SUPPORT", "PERFORMANCE", "COMPETITOR", "OTHER", name="churnreasoncategory", create_type=False), nullable=False),
        sa.Column("revenue_lost", sa.Numeric(12, 2), nullable=False),
        sa.Column("lifetime_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("retention_attempts", sa.JSON(), server_default="[]"),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("analyzed_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # commercial_marketing_plans (already has enum from 001)
    op.create_table(
        "commercial_marketing_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("icp_matrix_id", sa.Integer(), sa.ForeignKey("commercial_icp_matrix.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("objectives", sa.Text(), nullable=False),
        sa.Column("target_segments", sa.JSON(), server_default="[]"),
        sa.Column("budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("channels", sa.JSON(), server_default="[]"),
        sa.Column("kpis", sa.JSON(), server_default="[]"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "ACTIVE", "COMPLETED", name="marketingplanstatus", create_type=False), server_default="DRAFT"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # commercial_competition_matrix
    op.create_table(
        "commercial_competition_matrix",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("icp_matrix_id", sa.Integer(), sa.ForeignKey("commercial_icp_matrix.id"), nullable=True),
        sa.Column("competitor_name", sa.String(255), nullable=False),
        sa.Column("product_category", sa.String(255), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False),
        sa.Column("weaknesses", sa.Text(), nullable=False),
        sa.Column("pricing_model", sa.String(255), nullable=True),
        sa.Column("estimated_market_share", sa.Integer(), nullable=True),
        sa.Column("threat_level", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("commercial_competition_matrix")
    op.drop_table("commercial_marketing_plans")
    op.drop_table("commercial_churn_analysis")
    op.drop_table("commercial_handoffs")
    op.drop_table("commercial_quotes")

    op.execute("DROP TYPE IF EXISTS marketingplanstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS churnreasoncategory CASCADE;")
    op.execute("DROP TYPE IF EXISTS handoffstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS quotestatus CASCADE;")
