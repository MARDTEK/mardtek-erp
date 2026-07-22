"""Web dashboard route."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.web.deps import get_current_user_from_session
from app.web.utils import render

router = APIRouter(tags=["Web — Dashboard"])

# Module definitions: (prefix, name, code, table_name, label_column)
_MODULES: List[Dict[str, Any]] = [
    {"prefix": "/quality", "name": "Quality Management", "code": "P2",
     "tables": ["quality_documents", "quality_non_conformities", "quality_corrective_actions",
                "quality_audits", "quality_improvements"],
     "labels": ["Documents", "Non-Conformities", "Corrective Actions", "Audits", "Improvements"]},
    {"prefix": "/strategic", "name": "Strategic Planning", "code": "P1",
     "tables": ["strategic_quality_policies", "strategic_quality_objectives",
                "strategic_management_reviews"],
     "labels": ["Policies", "Objectives", "Mgmt Reviews"]},
    {"prefix": "/commercial", "name": "Commercial Sales", "code": "P3",
     "tables": ["commercial_leads", "commercial_proposals", "commercial_contracts"],
     "labels": ["Leads", "Proposals", "Contracts"]},
    {"prefix": "/development", "name": "Tech Development", "code": "P4",
     "tables": ["tech_product_roadmaps", "tech_release_plans", "tech_technical_specs"],
     "labels": ["Roadmaps", "Releases", "Specs"]},
    {"prefix": "/projects", "name": "PMO Projects", "code": "P5",
     "tables": ["pmo_projects", "pmo_deliverables_checklists", "pmo_follow_up_meetings"],
     "labels": ["Projects", "Deliverables", "Meetings"]},
    {"prefix": "/training", "name": "Training & Services", "code": "P6",
     "tables": ["training_plans", "training_courses", "training_sessions"],
     "labels": ["Plans", "Courses", "Sessions"]},
    {"prefix": "/hr", "name": "Human Resources", "code": "P7",
     "tables": ["hr_staff_register", "hr_job_descriptions", "hr_performance_evaluations"],
     "labels": ["Staff", "Job Desc", "Evaluations"]},
    {"prefix": "/infrastructure", "name": "Infrastructure & IT", "code": "P8",
     "tables": ["infra_requests", "infra_incident_reports", "infra_maintenance_records"],
     "labels": ["Requests", "Incidents", "Maintenance"]},
    {"prefix": "/procurement", "name": "Procurement", "code": "P9",
     "tables": ["procurement_purchase_requests", "procurement_supplier_register"],
     "labels": ["Purchases", "Suppliers"]},
    {"prefix": "/customer-satisfaction", "name": "Customer Experience", "code": "P10",
     "tables": ["cx_nps_surveys", "cx_complaints", "cx_escalations"] if False else
               ["cx_nps_surveys", "cx_complaints"],
     "labels": ["NPS", "Complaints"]},
    {"prefix": "/analytics", "name": "Analytics & Performance", "code": "P11",
     "tables": ["analytics_performance_indicators", "analytics_kpi_reports"],
     "labels": ["Indicators", "KPI Reports"]},
]


async def _count_table(db: AsyncSession, table_name: str) -> int:
    """Count non-deleted rows in a table."""
    from app.core.database import Base
    if table_name not in Base.metadata.tables:
        return 0
    table = Base.metadata.tables[table_name]
    has_soft_delete = "is_deleted" in [c.name for c in table.columns]
    query = select(func.count()).select_from(table)
    if has_soft_delete:
        query = query.where(table.c.is_deleted == False)  # noqa: E712
    result = await db.execute(query)
    return result.scalar() or 0


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session),
):
    """Render dashboard with module overview cards."""
    module_data = []
    for mod in _MODULES:
        counts = []
        for table_name in mod["tables"]:
            count = await _count_table(db, table_name)
            counts.append(count)
        total = sum(counts)
        details = list(zip(mod["labels"], counts))
        module_data.append({
            "prefix": mod["prefix"],
            "name": mod["name"],
            "code": mod["code"],
            "total": total,
            "details": details,
        })

    return render(request, "dashboard.html", {
        "modules": module_data,
        "page_title": "Dashboard",
    })
