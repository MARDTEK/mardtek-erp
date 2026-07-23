# MARDTEK ERP — Agent Instructions

## OKF Knowledge Bundle (MANDATORY)

The OKF bundle at `/home/mard/Proyectos/MARDTEK_OS/docs/sgc-okf/.okf/` is the **single source of truth** for all business requirements. Every SGC module's implementation MUST be a faithful reflection of this bundle.

**Before writing or modifying ANY module code**, read the corresponding OKF process file:

| Module (code dir) | OKF Process File | OKF Category |
|--------------------|-----------------|--------------|
| `strategic_planning` (P1) | `strategic/p1-strategic-management.md` | strategic |
| `quality_management` (P2) | `strategic/p2-quality-management.md` | strategic |
| `commercial_sales` (P3) | `operational/p3-commercial-management.md` | operational |
| `tech_development` (P4) | `operational/p4-design-development.md` | operational |
| `pmo_projects` (P5) | `operational/p5-project-execution.md` | operational |
| `training_services` (P6) | `operational/p6-training-development.md` | operational |
| `human_resources` (P7) | `support/p7-hr-management.md` | support |
| `infrastructure_it` (P8) | `support/p8-infrastructure-technology.md` | support |
| `procurement` (P9) | `support/p9-procurement-suppliers.md` | support |
| `customer_experience` (P10) | `measurement/p10-customer-satisfaction.md` | measurement |
| `analytics_performance` (P11) | `measurement/p11-data-analysis-performance.md` | measurement |

### What the OKF defines per process

Each process file contains:
- **Purpose**: What the process does
- **Scope**: What it covers
- **Document Inventory**: Every document type with prefix codes (SOP, FO, REG, PLN, MAT, etc.)
- **Interactions**: Cross-process data flows and dependencies

### Implementation rules

1. **Entities**: SQLAlchemy models MUST reflect the OKF document inventory. Each document type (SOP, FO, REG, PLN) maps to a domain entity or its fields.
2. **Prefixes**: Document prefix codes (e.g., SOP-P5-001, FO-P7-001) are part of the business domain. Include them in models and UI.
3. **Interactions**: Cross-module references (e.g., P5 receives from P3, delivers to P6) MUST be modeled as foreign keys or relationships.
4. **ISO mapping**: The OKF's ISO 9001:2015 clause alignment (standards.md) informs field requirements and validation rules.
5. **Product lines**: SERVICIOS and SAAS contexts shape which entities apply. Some processes span both.

### Reference files

- `standards.md` — ISO 9001:2015 clause mapping for all 11 processes
- `document-types.md` — Prefix conventions and naming standards
- `organization.md` — Company profile, QMS scope, product lines
- `getting-started.md` — Process interaction map and navigation

## Organization

- **Company**: MARDTEK — technology company
- **Product lines**: SERVICIOS (project-based) and SAAS (MicroSmart)
- **QMS**: 11 processes, ISO 9001:2015 aligned
- **Macro-categories**: Strategic (P1-P2), Operational (P3-P6), Support (P7-P9), Measurement (P10-P11)

## Architecture

- **Stack**: FastAPI + Jinja2 + HTMX + Alpine.js + TailwindCSS (server-rendered)
- **Auth**: Session-based with CSRF (not JWT for web routes)
- **Testing**: pytest with httpx.AsyncClient + ASGITransport
- **DB**: asyncpg + SQLAlchemy async, Alembic migrations
- **Modules**: Each has `domain/models.py`, `infrastructure/repositories.py`, `application/`, `interfaces/`

## Development Status (2026-07-23)

### Summary

| Metric | Total |
|--------|-------|
| SQLAlchemy models | 87 |
| API endpoints | 413 |
| Web routes (HTMX) | 225 |
| Jinja2 templates | 105 |
| Tests | 444 |
| Modules with frontend | 7/11 |

### Module Status

| OKF | Module | Models | API | Web UI | Templates | Tests | Status |
|-----|--------|--------|-----|--------|-----------|-------|--------|
| **P1** | Strategic Planning | 6 | 19 | ✅ 37 | ✅ 18 | 31 | **Substantial** |
| **P2** | Quality Management | 7 | 42 | ✅ 33 | ✅ 10 | 42 | **Substantial** |
| **P3** | Commercial Sales | 15 | 50 | ✅ 63 | ✅ 37 | 26 | **Substantial** |
| **P4** | Tech Development | 8 | 47 | ✅ 82 | ✅ 31 | 53 | **Substantial** |
| **P5** | PMO Projects | 8 | 32 | ✅ 5 | ✅ 4 | 29 | **Substantial** |
| **P6** | Training Services | 10 | 62 | ✅ 7 | ✅ 5 | 56 | **Substantial** |
| **P7** | Human Resources | 8 | 47 | ❌ | ❌ | 49 | **Partial** |
| **P8** | Infrastructure/IT | 7 | 29 | ❌ | ❌ | 29 | **Partial** |
| **P9** | Procurement | 6 | 32 | ❌ | ❌ | 27 | **Partial** |
| **P10** | Customer Experience | 7 | 26 | ❌ | ❌ | 40 | **Partial** |
| **P11** | Analytics/Performance | 5 | 27 | ✅ 8 | ✅ 9 | 32 | **Substantial** |

### Status Definitions

- **Substantial**: Models + API + Web UI + Templates + Tests. Ready for use.
- **Partial**: Models + API + Tests. Functional via API but no web interface.
- **Skeleton**: Models only, no routes.

### Remaining Work

#### Frontend (4 modules need web UI)

| Module | Web Routes | Templates | Priority |
|--------|-----------|-----------|----------|
| P7 Human Resources | 0 | 0 | Medium |
| P8 Infrastructure/IT | 0 | 0 | Medium |
| P9 Procurement | 0 | 0 | Medium |
| P10 Customer Experience | 0 | 0 | Low |

#### OKF Compliance Verification

Only P3 has been audited against its OKF bundle. Remaining modules need verification:
- P1, P2, P4, P5, P6, P11 (substantial modules)
- P7-P10 (partial modules)

#### Architecture Alignment (in progress)

The target state is Hexagonal Architecture (`application/services.py`, `interfaces/`, `infrastructure/repositories.py`).

- **P1, P2, P3, P4, P5, P6, P11**: ✅ Refactored to Hexagonal Architecture. API routes use Application Services and Repositories.
- **Other modules (P7-P10)**: ❌ Still need refactoring. Business logic currently lives in `domain/logic.py` and is executed directly in route handlers.
