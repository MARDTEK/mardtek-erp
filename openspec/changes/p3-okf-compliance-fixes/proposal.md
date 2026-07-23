---
change: p3-okf-compliance-fixes
status: proposed
created: '2026-07-23'
---

# P3 OKF Compliance Fixes

## Intent

Fix the P3 Commercial Sales module to be fully compliant with the OKF bundle (`p3-commercial-management.md`). The module already models all 16 document types, but has 3 incorrect OKF code references in docstrings and 2 missing API endpoints that leave the commercial lifecycle incomplete.

## Scope

### Issue A: Fix 3 incorrect docstring OKF codes

File: `app/modules/commercial_sales/domain/models.py`

| Line | Current | Correct | Why |
|------|---------|---------|-----|
| 71 | `FO-P3-001` | `SOP-P3-001` | Lead implements the qualification procedure, not a form |
| 110 | `FO-P3-002` | `SOP-P3-002` | Discovery records the analysis procedure result |
| 219 | `SOP-P3-009` | `SOP-P3-005` | Subscriptions are part of contract management |

### Issue B: Add `POST /quotes/{quote_id}/accept` endpoint

- Follow the pattern of `send_quote` (router.py line 480)
- Transition quote status from `sent` → `accepted`
- Set `accepted_at` timestamp
- Emit `QuoteAccepted` event
- Add `QuoteAccept` empty schema to `dto.py`

### Issue C: Add `POST /contracts` endpoint with `ContractCreate` schema

- Create `ContractCreate` schema in `dto.py`
- Auto-generate `contract_number` following `CTR-{timestamp}` pattern
- Auto-set `signed_at` to now
- Support both SOW and SUBSCRIPTION contract types

## Risks

- **Low risk**: Docstrings are comments only. New endpoints are purely additive.
- **No database migrations**: All fields already exist in models.
- **No breaking changes**: Existing endpoints untouched.

## Estimated Lines

~103 lines across 3 files + ~40 lines of tests.

## Tests Needed

- `POST /quotes/{id}/accept` — happy path + 404 + wrong status
- `POST /contracts` — happy path SOW + subscription + validation

## Dependencies

None. All changes self-contained in `commercial_sales` module.
