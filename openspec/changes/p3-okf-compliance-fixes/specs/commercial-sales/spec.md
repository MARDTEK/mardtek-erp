# Commercial Sales — P3 OKF Compliance Fixes

## ADDED Requirements

### Requirement: Quote Acceptance

The system MUST allow acceptance of a sent quote, transitioning its status and recording the acceptance timestamp. A `QuoteAccepted` event MUST be emitted upon successful acceptance.

#### Scenario: Accept a sent quote

- GIVEN a quote exists with status `sent`
- WHEN `POST /quotes/{quote_id}/accept` is called
- THEN the quote status transitions to `accepted`
- AND `accepted_at` is set to the current UTC timestamp
- AND a `QuoteAccepted` event is emitted with `quote_id` and `lead_id`

#### Scenario: Accept a non-existent quote

- GIVEN no quote exists with the given ID
- WHEN `POST /quotes/{quote_id}/accept` is called
- THEN a 404 response is returned with detail "Quote not found"

#### Scenario: Accept a quote that is not in sent status

- GIVEN a quote exists with status other than `sent` (e.g. `draft`, `accepted`, `rejected`)
- WHEN `POST /quotes/{quote_id}/accept` is called
- THEN a 400 response is returned with detail "Only sent quotes can be accepted"

---

### Requirement: Contract Creation

The system MUST allow creation of a contract from a lead. The contract number MUST be auto-generated following the `CTR-{timestamp}` pattern. The `signed_at` timestamp MUST be set automatically.

#### Scenario: Create a SOW contract

- GIVEN a lead exists with product line `SERVICIOS`
- WHEN `POST /contracts` is called with `lead_id`, `contract_type: sow`, `start_date`, `total_value`
- THEN a contract is created with `contract_type` = `sow`
- AND `contract_number` follows `CTR-{YYYYMMDDHHMMSS}` pattern
- AND `signed_at` is set to the current UTC timestamp
- AND `status` defaults to `active`

#### Scenario: Create a subscription contract

- GIVEN a lead exists with product line `SAAS`
- WHEN `POST /contracts` is called with `lead_id`, `contract_type: subscription`, `start_date`, `total_value`
- THEN a contract is created with `contract_type` = `subscription`
- AND all auto-generated fields are set as above

#### Scenario: Create contract for non-existent lead

- GIVEN no lead exists with the given `lead_id`
- WHEN `POST /contracts` is called
- THEN a 404 response is returned with detail "Lead not found"

#### Scenario: Create contract with invalid payload

- WHEN `POST /contracts` is called without required fields (`lead_id`, `contract_type`, `start_date`, `total_value`)
- THEN a 422 validation error is returned

---

## MODIFIED Requirements

### Requirement: Model OKF Code Accuracy

All domain model docstrings MUST reference the correct OKF document code from the P3 document inventory (`p3-commercial-management.md`).

(Previously: Three models referenced incorrect OKF codes)

#### Scenario: Lead model references SOP-P3-001

- GIVEN the Lead model in `domain/models.py`
- WHEN the docstring is inspected
- THEN it references `SOP-P3-001` (Lead qualification procedure)
- AND NOT `FO-P3-001` (Lead qualification form)

#### Scenario: Discovery model references SOP-P3-002

- GIVEN the Discovery model in `domain/models.py`
- WHEN the docstring is inspected
- THEN it references `SOP-P3-002` (Discovery and needs analysis)
- AND NOT `FO-P3-002` (Discovery questionnaire)

#### Scenario: SaasSubscription model references SOP-P3-005

- GIVEN the SaasSubscription model in `domain/models.py`
- WHEN the docstring is inspected
- THEN it references `SOP-P3-005` (Contract management — SOW/subscription)
- AND NOT `SOP-P3-009` (Churn analysis procedure)

---

## Schemas Added

### QuoteAccept

Empty schema (no payload). Mirrors `send_quote` pattern — status transition only.

### ContractCreate

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| lead_id | int | Yes | FK to commercial_leads |
| proposal_id | int | No | FK to commercial_proposals |
| contract_type | sow \| subscription | Yes | |
| start_date | date | Yes | |
| end_date | date | No | |
| total_value | Decimal | Yes | |
| monthly_value | Decimal | No | |
| sla_clauses | str | No | |

---

## Edge Cases

- **Quote already accepted**: Accepting an already-accepted quote returns 400.
- **Contract number collision**: Unlikely with timestamp pattern but no DB uniqueness guard on creation path beyond the unique index.
- **Lead status on contract creation**: Lead status is NOT auto-updated; the `win_lead` logic already handles this separately.
