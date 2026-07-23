# Tasks: P3 OKF Compliance Fixes

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~153 (103 code + 50 tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | auto-forecast |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | All changes + tests | PR 1 | `pytest tests/test_commercial.py -v` | httpx AsyncClient + ASGITransport (existing pattern) | Revert single PR — all changes in commercial_sales module only |

## Phase 1: Docstring Corrections

- [ ] 1.1 In `app/modules/commercial_sales/domain/models.py` line 71: change `FO-P3-001` to `SOP-P3-001` in Lead docstring
- [ ] 1.2 In `app/modules/commercial_sales/domain/models.py` line 110: change `FO-P3-002` to `SOP-P3-002` in Discovery docstring
- [ ] 1.3 In `app/modules/commercial_sales/domain/models.py` line 219: change `SOP-P3-009` to `SOP-P3-005` in SaasSubscription docstring

## Phase 2: Schemas

- [ ] 2.1 In `app/modules/commercial_sales/schemas/dto.py`: add `ContractCreate` class after `ContractResponse` (after line 138). Fields: lead_id (int), proposal_id (Optional[int]), contract_type (str, pattern sow|subscription), start_date (date), end_date (Optional[date]), total_value (Decimal), monthly_value (Optional[Decimal]), sla_clauses (Optional[str]). Import Decimal already present.
- [ ] 2.2 In `app/modules/commercial_sales/schemas/dto.py`: add `QuoteAccept` empty class after `QuoteResponse` (after line 287). Pattern: `class QuoteAccept(BaseModel): pass`

## Phase 3: Endpoints

- [ ] 3.1 In `app/modules/commercial_sales/router.py`: add import `ContractCreate, QuoteAccept` to the schemas import block (line 42-76). Insert after line 75.
- [ ] 3.2 In `app/modules/commercial_sales/router.py`: add `create_contract` endpoint after `get_contract` (after line 256). POST /contracts, status 201, RoleChecker admin/manager. Verify lead exists, auto-generate contract_number as CTR-{timestamp}, set signed_at, emit ContractCreated event. ~15 lines.
- [ ] 3.3 In `app/modules/commercial_sales/router.py`: add `accept_quote` endpoint after `send_quote` (after line 492). POST /quotes/{quote_id}/accept, RoleChecker admin/manager. Validate status==sent, set accepted_at, emit QuoteAccepted event. Follow send_quote pattern exactly. ~13 lines.

## Phase 4: Tests

- [ ] 4.1 In `tests/test_commercial.py`: add `TestQuoteAccept` class. Test methods: `test_accept_quote_happy_path` (create lead→quote→send→accept, assert status=accepted, accepted_at set), `test_accept_quote_not_found` (404), `test_accept_quote_wrong_status` (draft quote→400). ~20 lines.
- [ ] 4.2 In `tests/test_commercial.py`: add `TestCreateContract` class. Test methods: `test_create_contract_sow` (happy path, 201, contract_number starts with CTR-), `test_create_contract_subscription` (happy path), `test_create_contract_lead_not_found` (404), `test_create_contract_invalid_type` (422 validation error). ~30 lines.

## Implementation Order

1. Phase 1 (docstrings) — zero dependencies, pure comment fixes
2. Phase 2 (schemas) — no dependency on Phase 1, but needed by Phase 3
3. Phase 3 (endpoints) — depends on Phase 2 schemas being in place
4. Phase 4 (tests) — depends on all endpoints existing
