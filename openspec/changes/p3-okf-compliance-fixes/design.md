---
change: p3-okf-compliance-fixes
status: designed
created: '2026-07-23'
---

# P3 OKF Compliance Fixes — Technical Design

## Change A: Docstring Corrections

**File**: `app/modules/commercial_sales/domain/models.py`

| Line | Current | New |
|------|---------|-----|
| 71 | `FO-P3-001` | `SOP-P3-001` |
| 110 | `FO-P3-002` | `SOP-P3-002` |
| 219 | `SOP-P3-009` | `SOP-P3-005` |

## Change B: Quote Acceptance Endpoint

### Schema (`dto.py`)
```python
class QuoteAccept(BaseModel):
    pass
```

### Endpoint (`router.py`)
- `POST /quotes/{quote_id}/accept`
- RoleChecker: admin, manager
- Guard: only `sent` quotes → `accepted`
- Sets `accepted_at` timestamp
- Emits `QuoteAccepted` event

## Change C: Contract Creation Endpoint

### Schema (`dto.py`)
```python
class ContractCreate(BaseModel):
    lead_id: int
    proposal_id: Optional[int] = None
    contract_type: str = Field(..., pattern=r"^(sow|subscription)$")
    start_date: date
    end_date: Optional[date] = None
    total_value: Decimal
    monthly_value: Optional[Decimal] = None
    sla_clauses: Optional[str] = None
```

### Endpoint (`router.py`)
- `POST /contracts` (status 201)
- RoleChecker: admin, manager
- Auto-generates: `contract_number` (CTR-{timestamp}), `signed_at` (now)
- Validates: lead_id exists
- Emits `ContractCreated` event

## File Summary

| File | Changes | ~Lines |
|------|---------|--------|
| `domain/models.py` | 3 docstring fixes | 3 |
| `schemas/dto.py` | QuoteAccept + ContractCreate | 20 |
| `router.py` | 2 endpoints | 45 |
| **Total** | | **68** |
