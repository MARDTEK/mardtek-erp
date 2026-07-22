from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import RoleChecker, get_current_user
from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.core.pagination import PaginationParams, paginate
from app.modules.infrastructure_it.domain.logic import (
    get_open_incidents_by_severity,
    transition_maintenance_status,
)
from app.modules.infrastructure_it.domain.models import (
    AvailabilityReport,
    BusinessContinuityPlan,
    IncidentReport,
    InfrastructureRequest,
    MaintenanceRecord,
    SecurityIncident,
    SlaAgreement,
)
from app.modules.infrastructure_it.schemas.dto import (
    AvailabilityReportCreate,
    AvailabilityReportResponse,
    BusinessContinuityPlanCreate,
    BusinessContinuityPlanResponse,
    BusinessContinuityPlanUpdate,
    IncidentReportCreate,
    IncidentReportResponse,
    IncidentReportUpdate,
    InfrastructureRequestCreate,
    InfrastructureRequestResponse,
    InfrastructureRequestUpdate,
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceStatusTransition,
    MaintenanceRecordUpdate,
    SecurityIncidentCreate,
    SecurityIncidentResponse,
    SecurityIncidentUpdate,
    SlaAgreementCreate,
    SlaAgreementResponse,
    SlaAgreementUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# ─── Infrastructure Requests ─────────────────────────────────────────────

@router.get("/requests", response_model=List[InfrastructureRequestResponse])
async def list_requests(
    resource_type: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(InfrastructureRequest)
    if resource_type:
        stmt = stmt.where(InfrastructureRequest.resource_type == resource_type)
    if status_filter:
        stmt = stmt.where(InfrastructureRequest.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(InfrastructureRequest.code), page))
    return list(result.scalars().all())


@router.post("/requests", response_model=InfrastructureRequestResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_request(payload: InfrastructureRequestCreate, db: AsyncSession = Depends(get_db)):
    req = InfrastructureRequest(**payload.model_dump())
    db.add(req)
    await db.flush()
    return req


@router.get("/requests/{request_id}", response_model=InfrastructureRequestResponse)
async def get_request(request_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InfrastructureRequest).where(InfrastructureRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Infrastructure request not found")
    return req


@router.patch("/requests/{request_id}", response_model=InfrastructureRequestResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_request(
    request_id: int,
    payload: InfrastructureRequestUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(InfrastructureRequest).where(InfrastructureRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Infrastructure request not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    await db.flush()
    return req


# ─── SLA Agreements ──────────────────────────────────────────────────────

@router.get("/sla-agreements", response_model=List[SlaAgreementResponse])
async def list_sla_agreements(
    provider: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(SlaAgreement)
    if provider:
        stmt = stmt.where(SlaAgreement.provider.ilike(f"%{provider}%"))
    if status_filter:
        stmt = stmt.where(SlaAgreement.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(SlaAgreement.code), page))
    return list(result.scalars().all())


@router.post("/sla-agreements", response_model=SlaAgreementResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_sla_agreement(payload: SlaAgreementCreate, db: AsyncSession = Depends(get_db)):
    sla = SlaAgreement(**payload.model_dump())
    db.add(sla)
    await db.flush()
    return sla


@router.get("/sla-agreements/{sla_id}", response_model=SlaAgreementResponse)
async def get_sla_agreement(sla_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SlaAgreement).where(SlaAgreement.id == sla_id))
    sla = result.scalar_one_or_none()
    if not sla:
        raise HTTPException(status_code=404, detail="SLA agreement not found")
    return sla


@router.patch("/sla-agreements/{sla_id}", response_model=SlaAgreementResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_sla_agreement(
    sla_id: int,
    payload: SlaAgreementUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SlaAgreement).where(SlaAgreement.id == sla_id))
    sla = result.scalar_one_or_none()
    if not sla:
        raise HTTPException(status_code=404, detail="SLA agreement not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sla, field, value)
    await db.flush()
    return sla


# ─── Incident Reports ────────────────────────────────────────────────────

@router.get("/incidents", response_model=List[IncidentReportResponse])
async def list_incidents(
    severity: str | None = None,
    status_filter: str | None = None,
    service: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(IncidentReport)
    if severity:
        stmt = stmt.where(IncidentReport.severity == severity)
    if status_filter:
        stmt = stmt.where(IncidentReport.status == status_filter)
    if service:
        stmt = stmt.where(IncidentReport.service.ilike(f"%{service}%"))
    result = await db.execute(paginate(stmt.order_by(IncidentReport.created_at.desc()), page))
    return list(result.scalars().all())


@router.get("/incidents/open-by-severity")
async def open_incidents_by_severity(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, int]:
    return await get_open_incidents_by_severity(db)


@router.post("/incidents", response_model=IncidentReportResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def create_incident(payload: IncidentReportCreate, db: AsyncSession = Depends(get_db)):
    inc = IncidentReport(**payload.model_dump())
    db.add(inc)
    await db.flush()

    # Emit IncidentReported for P1 and P2 severity
    if inc.severity.value in ("P1", "P2"):
        await event_bus.emit(
            Event(
                name="IncidentReported",
                payload={
                    "id": inc.id,
                    "code": inc.code,
                    "service": inc.service,
                    "severity": inc.severity.value,
                    "status": inc.status.value,
                },
                source_module="infrastructure_it",
            )
        )

    return inc


@router.get("/incidents/{incident_id}", response_model=IncidentReportResponse)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IncidentReport).where(IncidentReport.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident report not found")
    return inc


@router.patch("/incidents/{incident_id}", response_model=IncidentReportResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_incident(
    incident_id: int,
    payload: IncidentReportUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IncidentReport).where(IncidentReport.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident report not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inc, field, value)
    # Auto-set resolved_at when status transitions to resolved
    if payload.status == "resolved" and not inc.resolved_at:
        from datetime import datetime, timezone
        inc.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return inc


# ─── Availability Reports ────────────────────────────────────────────────

@router.get("/availability-reports", response_model=List[AvailabilityReportResponse])
async def list_availability_reports(
    service: str | None = None,
    sla_met: bool | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(AvailabilityReport)
    if service:
        stmt = stmt.where(AvailabilityReport.service.ilike(f"%{service}%"))
    if sla_met is not None:
        stmt = stmt.where(AvailabilityReport.sla_met == sla_met)
    result = await db.execute(paginate(stmt.order_by(AvailabilityReport.created_at.desc()), page))
    return list(result.scalars().all())


@router.post(
    "/availability-reports",
    response_model=AvailabilityReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_availability_report(payload: AvailabilityReportCreate, db: AsyncSession = Depends(get_db)):
    report = AvailabilityReport(**payload.model_dump())
    db.add(report)
    await db.flush()

    # Emit SLABreach when SLA target is not met
    if not report.sla_met:
        await event_bus.emit(
            Event(
                name="SLABreach",
                payload={
                    "id": report.id,
                    "service": report.service,
                    "uptime_percent": report.uptime_percent,
                    "downtime_minutes": report.downtime_minutes,
                    "period_start": report.period_start.isoformat(),
                    "period_end": report.period_end.isoformat(),
                },
                source_module="infrastructure_it",
            )
        )

    return report


@router.get("/availability-reports/{report_id}", response_model=AvailabilityReportResponse)
async def get_availability_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AvailabilityReport).where(AvailabilityReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Availability report not found")
    return report


# ─── Business Continuity Plans ───────────────────────────────────────────

@router.get("/continuity-plans", response_model=List[BusinessContinuityPlanResponse])
async def list_continuity_plans(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(BusinessContinuityPlan)
    if status_filter:
        stmt = stmt.where(BusinessContinuityPlan.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(BusinessContinuityPlan.code), page))
    return list(result.scalars().all())


@router.post(
    "/continuity-plans",
    response_model=BusinessContinuityPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_continuity_plan(payload: BusinessContinuityPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = BusinessContinuityPlan(**payload.model_dump())
    db.add(plan)
    await db.flush()
    return plan


@router.get("/continuity-plans/{plan_id}", response_model=BusinessContinuityPlanResponse)
async def get_continuity_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessContinuityPlan).where(BusinessContinuityPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Business continuity plan not found")
    return plan


@router.patch("/continuity-plans/{plan_id}", response_model=BusinessContinuityPlanResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_continuity_plan(
    plan_id: int,
    payload: BusinessContinuityPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(BusinessContinuityPlan).where(BusinessContinuityPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Business continuity plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()
    return plan


# ─── Security Incidents ──────────────────────────────────────────────────

@router.get("/security-incidents", response_model=List[SecurityIncidentResponse])
async def list_security_incidents(
    incident_type: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(SecurityIncident)
    if incident_type:
        stmt = stmt.where(SecurityIncident.incident_type == incident_type)
    if status_filter:
        stmt = stmt.where(SecurityIncident.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(SecurityIncident.created_at.desc()), page))
    return list(result.scalars().all())


@router.post(
    "/security-incidents",
    response_model=SecurityIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_security_incident(payload: SecurityIncidentCreate, db: AsyncSession = Depends(get_db)):
    inc = SecurityIncident(**payload.model_dump())
    db.add(inc)
    await db.flush()
    return inc


@router.get("/security-incidents/{incident_id}", response_model=SecurityIncidentResponse)
async def get_security_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SecurityIncident).where(SecurityIncident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Security incident not found")
    return inc


@router.patch("/security-incidents/{incident_id}", response_model=SecurityIncidentResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_security_incident(
    incident_id: int,
    payload: SecurityIncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SecurityIncident).where(SecurityIncident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Security incident not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inc, field, value)
    await db.flush()
    return inc


# ─── Maintenance Records ─────────────────────────────────────────────────

@router.get("/maintenance-records", response_model=List[MaintenanceRecordResponse])
async def list_maintenance_records(
    asset: str | None = None,
    maintenance_type: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    page: PaginationParams = Depends(),
):
    stmt = select(MaintenanceRecord)
    if asset:
        stmt = stmt.where(MaintenanceRecord.asset.ilike(f"%{asset}%"))
    if maintenance_type:
        stmt = stmt.where(MaintenanceRecord.maintenance_type == maintenance_type)
    if status_filter:
        stmt = stmt.where(MaintenanceRecord.status == status_filter)
    result = await db.execute(paginate(stmt.order_by(MaintenanceRecord.scheduled_date.desc()), page))
    return list(result.scalars().all())


@router.post(
    "/maintenance-records",
    response_model=MaintenanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def create_maintenance_record(payload: MaintenanceRecordCreate, db: AsyncSession = Depends(get_db)):
    record = MaintenanceRecord(**payload.model_dump())
    db.add(record)
    await db.flush()
    return record


@router.get("/maintenance-records/{record_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance_record(record_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return record


@router.patch("/maintenance-records/{record_id}", response_model=MaintenanceRecordResponse, dependencies=[Depends(RoleChecker("admin", "manager"))])
async def update_maintenance_record(
    record_id: int,
    payload: MaintenanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    return record


@router.patch(
    "/maintenance-records/{record_id}/transition",
    response_model=MaintenanceRecordResponse,
    dependencies=[Depends(RoleChecker("admin", "manager"))],
)
async def transition_maintenance_record(
    record_id: int,
    payload: MaintenanceStatusTransition,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    updated = await transition_maintenance_status(
        record,
        target_status=payload.target_status,
        performed_by=payload.performed_by,
        completed_date=payload.completed_date,
    )
    if not updated:
        raise HTTPException(
            status_code=422,
            detail="Invalid status transition. SCHEDULED→IN_PROGRESS always allowed; IN_PROGRESS→COMPLETED requires performed_by and completed_date.",
        )

    await db.flush()
    return record
