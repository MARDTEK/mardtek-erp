from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.event_bus import Event, event_bus
from app.modules.customer_experience.domain.logic import (
    auto_categorize_nps,
    calculate_csat,
    calculate_ces,
    calculate_nps,
    get_complaints_by_status,
)
from app.modules.customer_experience.domain.models import (
    CesSurvey,
    ChurnReasonCategory,
    ComplaintClaim,
    ComplaintRegister,
    ComplaintStatus,
    ComplaintType,
    CsatSurvey,
    EscalationLevel,
    ExitInterview,
    NpsCategory,
    NpsSurvey,
    SatisfactionReport,
)
from app.modules.customer_experience.schemas.dto import (
    CesSurveyCreate,
    CesSurveyResponse,
    ComplaintClaimCreate,
    ComplaintClaimResponse,
    ComplaintClaimUpdate,
    ComplaintRegisterCreate,
    ComplaintRegisterResponse,
    CsatSurveyCreate,
    CsatSurveyResponse,
    ExitInterviewCreate,
    ExitInterviewResponse,
    NpsSurveyCreate,
    NpsSurveyResponse,
    SatisfactionReportCreate,
    SatisfactionReportResponse,
)

router = APIRouter()

NPS_TARGET: int = 60  # SGC minimum threshold defined in P10


# ─── NPS Surveys ─────────────────────────────────────────────────────────

@router.get("/nps-surveys", response_model=List[NpsSurveyResponse])
async def list_nps_surveys(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NpsSurvey)
    if category:
        stmt = stmt.where(NpsSurvey.category == category)
    result = await db.execute(stmt.order_by(NpsSurvey.responded_at.desc()))
    return list(result.scalars().all())


@router.post("/nps-surveys", response_model=NpsSurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_nps_survey(payload: NpsSurveyCreate, db: AsyncSession = Depends(get_db)):
    category = auto_categorize_nps(payload.score)
    survey = NpsSurvey(**payload.model_dump(exclude={"score"}), score=payload.score, category=category)
    db.add(survey)
    await db.flush()

    # Check NPS threshold — calculate rolling NPS and emit if breached
    result = await db.execute(select(NpsSurvey.score))
    all_scores = [row[0] for row in result.all()]
    current_nps = calculate_nps(all_scores)
    if current_nps < NPS_TARGET:
        await event_bus.emit(Event(
            name="NPSThresholdBreached",
            payload={
                "survey_id": survey.id,
                "survey_code": survey.code,
                "score": survey.score,
                "current_nps": current_nps,
                "threshold": NPS_TARGET,
                "customer_email": survey.customer_email,
            },
            source_module="customer_experience",
        ))
    return survey


@router.get("/nps-surveys/{survey_id}", response_model=NpsSurveyResponse)
async def get_nps_survey(survey_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NpsSurvey).where(NpsSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="NPS survey not found")
    return survey


# ─── CSAT Surveys ────────────────────────────────────────────────────────

@router.get("/csat-surveys", response_model=List[CsatSurveyResponse])
async def list_csat_surveys(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CsatSurvey)
    if project_id:
        stmt = stmt.where(CsatSurvey.project_id == project_id)
    result = await db.execute(stmt.order_by(CsatSurvey.responded_at.desc()))
    return list(result.scalars().all())


@router.post("/csat-surveys", response_model=CsatSurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_csat_survey(payload: CsatSurveyCreate, db: AsyncSession = Depends(get_db)):
    survey = CsatSurvey(**payload.model_dump())
    db.add(survey)
    await db.flush()
    return survey


@router.get("/csat-surveys/{survey_id}", response_model=CsatSurveyResponse)
async def get_csat_survey(survey_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CsatSurvey).where(CsatSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="CSAT survey not found")
    return survey


# ─── CES Surveys ─────────────────────────────────────────────────────────

@router.get("/ces-surveys", response_model=List[CesSurveyResponse])
async def list_ces_surveys(
    subscription_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CesSurvey)
    if subscription_id:
        stmt = stmt.where(CesSurvey.subscription_id == subscription_id)
    result = await db.execute(stmt.order_by(CesSurvey.responded_at.desc()))
    return list(result.scalars().all())


@router.post("/ces-surveys", response_model=CesSurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_ces_survey(payload: CesSurveyCreate, db: AsyncSession = Depends(get_db)):
    survey = CesSurvey(**payload.model_dump())
    db.add(survey)
    await db.flush()
    return survey


@router.get("/ces-surveys/{survey_id}", response_model=CesSurveyResponse)
async def get_ces_survey(survey_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CesSurvey).where(CesSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="CES survey not found")
    return survey


# ─── Complaints / Claims ─────────────────────────────────────────────────

@router.get("/complaints", response_model=List[ComplaintClaimResponse])
async def list_complaints(
    status_filter: str | None = None,
    type_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplaintClaim)
    if status_filter:
        stmt = stmt.where(ComplaintClaim.status == status_filter)
    if type_filter:
        stmt = stmt.where(ComplaintClaim.type == type_filter)
    result = await db.execute(stmt.order_by(ComplaintClaim.created_at.desc()))
    return list(result.scalars().all())


@router.post("/complaints", response_model=ComplaintClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(payload: ComplaintClaimCreate, db: AsyncSession = Depends(get_db)):
    complaint = ComplaintClaim(**payload.model_dump())
    db.add(complaint)
    await db.flush()

    # Emit ComplaintFiled event — linked to P2 Quality Management
    await event_bus.emit(Event(
        name="ComplaintFiled",
        payload={
            "complaint_id": complaint.id,
            "code": complaint.code,
            "customer_email": complaint.customer_email,
            "type": complaint.type.value if isinstance(complaint.type, ComplaintType) else complaint.type,
            "nc_id": complaint.nc_id,
            "escalation_level": complaint.escalation_level,
        },
        source_module="customer_experience",
    ))
    return complaint


@router.get("/complaints/{complaint_id}", response_model=ComplaintClaimResponse)
async def get_complaint(complaint_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ComplaintClaim).where(ComplaintClaim.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/complaints/{complaint_id}", response_model=ComplaintClaimResponse)
async def update_complaint(
    complaint_id: int,
    payload: ComplaintClaimUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ComplaintClaim).where(ComplaintClaim.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(complaint, field, value)
    await db.flush()
    return complaint


@router.get("/complaints/by-status/{status}", response_model=List[ComplaintClaimResponse])
async def list_complaints_by_status(status: str, db: AsyncSession = Depends(get_db)):
    return await get_complaints_by_status(db, status)


# ─── Complaint Register ──────────────────────────────────────────────────

@router.get("/complaint-register", response_model=List[ComplaintRegisterResponse])
async def list_complaint_register(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ComplaintRegister)
    if category:
        stmt = stmt.where(ComplaintRegister.category == category)
    result = await db.execute(stmt.order_by(ComplaintRegister.registered_at.desc()))
    return list(result.scalars().all())


@router.post(
    "/complaint-register",
    response_model=ComplaintRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_complaint_register(payload: ComplaintRegisterCreate, db: AsyncSession = Depends(get_db)):
    # Verify linked complaint exists
    comp_result = await db.execute(
        select(ComplaintClaim).where(ComplaintClaim.id == payload.complaint_id)
    )
    if not comp_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Linked complaint not found")

    entry = ComplaintRegister(**payload.model_dump())
    db.add(entry)
    await db.flush()
    return entry


@router.get("/complaint-register/{entry_id}", response_model=ComplaintRegisterResponse)
async def get_complaint_register_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ComplaintRegister).where(ComplaintRegister.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Complaint register entry not found")
    return entry


# ─── Exit Interviews ─────────────────────────────────────────────────────

@router.get("/exit-interviews", response_model=List[ExitInterviewResponse])
async def list_exit_interviews(
    churn_reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExitInterview)
    if churn_reason:
        stmt = stmt.where(ExitInterview.churn_reason_category == churn_reason)
    result = await db.execute(stmt.order_by(ExitInterview.interview_date.desc()))
    return list(result.scalars().all())


@router.post("/exit-interviews", response_model=ExitInterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_exit_interview(payload: ExitInterviewCreate, db: AsyncSession = Depends(get_db)):
    interview = ExitInterview(**payload.model_dump())
    db.add(interview)
    await db.flush()
    return interview


@router.get("/exit-interviews/{interview_id}", response_model=ExitInterviewResponse)
async def get_exit_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExitInterview).where(ExitInterview.id == interview_id))
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Exit interview not found")
    return interview


# ─── Satisfaction Reports ────────────────────────────────────────────────

@router.get("/reports", response_model=List[SatisfactionReportResponse])
async def list_reports(
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SatisfactionReport)
    if period:
        stmt = stmt.where(SatisfactionReport.period == period)
    result = await db.execute(stmt.order_by(SatisfactionReport.created_at.desc()))
    return list(result.scalars().all())


@router.post("/reports", response_model=SatisfactionReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(payload: SatisfactionReportCreate, db: AsyncSession = Depends(get_db)):
    report = SatisfactionReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    return report


@router.get("/reports/{report_id}", response_model=SatisfactionReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SatisfactionReport).where(SatisfactionReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Satisfaction report not found")
    return report


# ─── Analytics ───────────────────────────────────────────────────────────

@router.get("/analytics/nps")
async def analytics_nps(db: AsyncSession = Depends(get_db)):
    """Calculate current NPS across all surveys."""
    result = await db.execute(select(NpsSurvey.score))
    scores = [row[0] for row in result.all()]
    return {
        "nps": calculate_nps(scores),
        "total_responses": len(scores),
        "threshold": NPS_TARGET,
        "breached": calculate_nps(scores) < NPS_TARGET if scores else None,
    }


@router.get("/analytics/csat")
async def analytics_csat(db: AsyncSession = Depends(get_db)):
    """Calculate current CSAT average across all service surveys."""
    result = await db.execute(select(CsatSurvey.score))
    scores = [row[0] for row in result.all()]
    return {
        "csat": calculate_csat(scores),
        "total_responses": len(scores),
    }


@router.get("/analytics/ces")
async def analytics_ces(db: AsyncSession = Depends(get_db)):
    """Calculate current CES average across all effort surveys."""
    result = await db.execute(select(CesSurvey.score))
    scores = [row[0] for row in result.all()]
    return {
        "ces": calculate_ces(scores),
        "total_responses": len(scores),
    }
