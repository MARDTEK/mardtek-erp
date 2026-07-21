"""initial: all 11 SGC modules

Revision ID: 001
Revises: 
Create Date: 2026-07-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""CREATE TYPE actionstatus AS ENUM ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED');""")
    op.execute("""CREATE TYPE auditresult AS ENUM ('PASS', 'MINOR_NC', 'MAJOR_NC', 'CRITICAL_NC');""")
    op.execute("""CREATE TYPE auditstatus AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE certstatus AS ENUM ('ACTIVE', 'EXPIRED', 'REVOKED');""")
    op.execute("""CREATE TYPE checkliststatus AS ENUM ('IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE churnreasoncategory AS ENUM ('PRICE', 'PRODUCT_FIT', 'SUPPORT', 'PERFORMANCE', 'COMPETITOR', 'OTHER');""")
    op.execute("""CREATE TYPE closurestatus AS ENUM ('OPEN', 'CLOSED');""")
    op.execute("""CREATE TYPE complaintstatus AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED');""")
    op.execute("""CREATE TYPE complainttype AS ENUM ('COMPLAINT', 'CLAIM');""")
    op.execute("""CREATE TYPE continuityplanstatus AS ENUM ('DRAFT', 'REVIEWED', 'APPROVED');""")
    op.execute("""CREATE TYPE contracttype AS ENUM ('SOW', 'SUBSCRIPTION');""")
    op.execute("""CREATE TYPE coursemodality AS ENUM ('ONLINE', 'PRESENTIAL', 'HYBRID');""")
    op.execute("""CREATE TYPE coursestatus AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');""")
    op.execute("""CREATE TYPE crstatus AS ENUM ('SUBMITTED', 'APPROVED', 'REJECTED');""")
    op.execute("""CREATE TYPE deploymentenvironment AS ENUM ('DEV', 'STAGING', 'PRODUCTION');""")
    op.execute("""CREATE TYPE deploymentstatus AS ENUM ('SUCCESS', 'FAILED', 'ROLLED_BACK');""")
    op.execute("""CREATE TYPE documentstatus AS ENUM ('DRAFT', 'REVIEWED', 'APPROVED', 'OBSOLETE');""")
    op.execute("""CREATE TYPE evaluationstatus AS ENUM ('DRAFT', 'SUBMITTED', 'COMPLETED');""")
    op.execute("""CREATE TYPE frequency AS ENUM ('MONTHLY', 'QUARTERLY', 'YEARLY');""")
    op.execute("""CREATE TYPE handoverstatus AS ENUM ('PENDING', 'SIGNED');""")
    op.execute("""CREATE TYPE hr_contract_type AS ENUM ('PERMANENT', 'CONTRACTOR', 'INTERN');""")
    op.execute("""CREATE TYPE hr_incident_status AS ENUM ('OPEN', 'RESOLVED', 'CLOSED');""")
    op.execute("""CREATE TYPE idpstatus AS ENUM ('ACTIVE', 'COMPLETED');""")
    op.execute("""CREATE TYPE improvementstatus AS ENUM ('PROPOSED', 'APPROVED', 'IMPLEMENTED', 'EVALUATED');""")
    op.execute("""CREATE TYPE incidentseverity AS ENUM ('P1', 'P2', 'P3', 'P4');""")
    op.execute("""CREATE TYPE incidentstatus AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED');""")
    op.execute("""CREATE TYPE incidenttype AS ENUM ('WARNING', 'ACCIDENT', 'VIOLATION', 'GRIEVANCE');""")
    op.execute("""CREATE TYPE inductioncheckliststatus AS ENUM ('IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE leadstatus AS ENUM ('NEW', 'QUALIFYING', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION', 'WON', 'LOST', 'DISQUALIFIED');""")
    op.execute("""CREATE TYPE maintenancestatus AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE maintenancetype AS ENUM ('PREVENTIVE', 'CORRECTIVE', 'UPGRADE');""")
    op.execute("""CREATE TYPE manualstatus AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');""")
    op.execute("""CREATE TYPE marketingplanstatus AS ENUM ('DRAFT', 'ACTIVE', 'COMPLETED');""")
    op.execute("""CREATE TYPE ncseverity AS ENUM ('MINOR', 'MAJOR', 'CRITICAL');""")
    op.execute("""CREATE TYPE ncstatus AS ENUM ('OPEN', 'INVESTIGATING', 'CORRECTIVE_ACTION', 'VERIFICATION', 'CLOSED');""")
    op.execute("""CREATE TYPE needpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH');""")
    op.execute("""CREATE TYPE needstatus AS ENUM ('IDENTIFIED', 'IN_REVIEW', 'APPROVED', 'COMPLETED');""")
    op.execute("""CREATE TYPE npscategory AS ENUM ('PROMOTER', 'PASSIVE', 'DETRACTOR');""")
    op.execute("""CREATE TYPE objectivestatus AS ENUM ('ON_TRACK', 'AT_RISK', 'BEHIND', 'ACHIEVED');""")
    op.execute("""CREATE TYPE onboardingstatus AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE personnelrequeststatus AS ENUM ('OPEN', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'FILLED');""")
    op.execute("""CREATE TYPE planstatus AS ENUM ('DRAFT', 'ACTIVE', 'COMPLETED');""")
    op.execute("""CREATE TYPE pmo_plan_status AS ENUM ('DRAFT', 'APPROVED');""")
    op.execute("""CREATE TYPE policystatus AS ENUM ('DRAFT', 'REVIEWED', 'APPROVED', 'OBSOLETE');""")
    op.execute("""CREATE TYPE proc_evaluation_status AS ENUM ('DRAFT', 'COMPLETED');""")
    op.execute("""CREATE TYPE productline AS ENUM ('SERVICIOS', 'SAAS');""")
    op.execute("""CREATE TYPE projectstatus AS ENUM ('KICKED_OFF', 'IN_EXECUTION', 'CLOSED', 'ON_HOLD');""")
    op.execute("""CREATE TYPE purchaserequeststatus AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'ORDERED');""")
    op.execute("""CREATE TYPE releasestatus AS ENUM ('PLANNED', 'IN_PROGRESS', 'DEPLOYED', 'ROLLED_BACK');""")
    op.execute("""CREATE TYPE reportstatus AS ENUM ('DRAFT', 'FINAL');""")
    op.execute("""CREATE TYPE requeststatus AS ENUM ('SUBMITTED', 'APPROVED', 'PROVISIONED', 'REJECTED');""")
    op.execute("""CREATE TYPE roadmapstatus AS ENUM ('DRAFT', 'PUBLISHED');""")
    op.execute("""CREATE TYPE securityincidentstatus AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED');""")
    op.execute("""CREATE TYPE securityincidenttype AS ENUM ('BREACH', 'MALWARE', 'PHISHING', 'UNAUTHORIZED_ACCESS', 'OTHER');""")
    op.execute("""CREATE TYPE sessionstatus AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');""")
    op.execute("""CREATE TYPE slastatus AS ENUM ('ACTIVE', 'EXPIRED', 'TERMINATED');""")
    op.execute("""CREATE TYPE specstatus AS ENUM ('DRAFT', 'REVIEWED', 'APPROVED');""")
    op.execute("""CREATE TYPE staffstatus AS ENUM ('ACTIVE', 'TERMINATED', 'ON_LEAVE');""")
    op.execute("""CREATE TYPE subscriptionstatus AS ENUM ('TRIAL', 'ACTIVE', 'SUSPENDED', 'CANCELLED', 'CHURNED');""")
    op.execute("""CREATE TYPE subscriptiontier AS ENUM ('BASIC', 'PROFESSIONAL', 'ENTERPRISE');""")
    op.execute("""CREATE TYPE sunsetstatus AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED');""")
    op.execute("""CREATE TYPE supplierstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED');""")
    op.execute("""CREATE TYPE testtype AS ENUM ('UNIT', 'INTEGRATION', 'E2E', 'REGRESSION');""")
    op.execute("""CREATE TYPE trenddirection AS ENUM ('UP', 'DOWN', 'FLAT', 'VOLATILE');""")
    op.execute("""CREATE TYPE uatstatus AS ENUM ('PENDING', 'SIGNED', 'REJECTED');""")
    op.execute("""CREATE TYPE videostatus AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');""")

    op.execute("""
CREATE TABLE quality_non_conformities (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	source VARCHAR(50) NOT NULL, 
	source_ref VARCHAR(50), 
	description TEXT NOT NULL, 
	severity ncseverity NOT NULL, 
	root_cause TEXT, 
	status ncstatus NOT NULL, 
	reported_by VARCHAR(255) NOT NULL, 
	reported_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_labor_incidents (
	id SERIAL NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	incident_type incidenttype NOT NULL, 
	description TEXT NOT NULL, 
	resolution TEXT, 
	status hr_incident_status NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_personnel_requests (
	id SERIAL NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	requested_by VARCHAR(255) NOT NULL, 
	job_title VARCHAR(255) NOT NULL, 
	department VARCHAR(255) NOT NULL, 
	justification TEXT NOT NULL, 
	budget NUMERIC(12, 2) NOT NULL, 
	status personnelrequeststatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE training_user_manuals (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	product VARCHAR(255) NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	content_url VARCHAR(500) NOT NULL, 
	status manualstatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_qms_scope (
	id SERIAL NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	scope_description TEXT NOT NULL, 
	exclusions TEXT, 
	applicable_normative TEXT NOT NULL, 
	approved_by VARCHAR(255), 
	approved_at TIMESTAMP WITH TIME ZONE, 
	is_current BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_security_incidents (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	incident_type securityincidenttype NOT NULL, 
	description TEXT NOT NULL, 
	impact TEXT NOT NULL, 
	containment TEXT NOT NULL, 
	status securityincidentstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE analytics_performance_indicators (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	process_code VARCHAR(3) NOT NULL, 
	formula TEXT, 
	target_value FLOAT, 
	unit VARCHAR(50), 
	frequency frequency NOT NULL, 
	owner VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE commercial_leads (
	id SERIAL NOT NULL, 
	company VARCHAR(255) NOT NULL, 
	contact_name VARCHAR(255) NOT NULL, 
	contact_email VARCHAR(255) NOT NULL, 
	contact_phone VARCHAR(50), 
	source VARCHAR(100) NOT NULL, 
	icp_match_score INTEGER, 
	status leadstatus NOT NULL, 
	product_line VARCHAR(20) NOT NULL, 
	estimated_value NUMERIC(12, 2), 
	assigned_to VARCHAR(255), 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE analytics_performance_dashboards (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	layout JSON, 
	filters JSON, 
	is_default BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_complaints (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255) NOT NULL, 
	contract_id INTEGER, 
	type complainttype NOT NULL, 
	description TEXT NOT NULL, 
	desired_outcome TEXT, 
	status complaintstatus NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	escalation_level INTEGER NOT NULL, 
	nc_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE quality_process_owners (
	id SERIAL NOT NULL, 
	process_code VARCHAR(3) NOT NULL, 
	process_name VARCHAR(255) NOT NULL, 
	owner_name VARCHAR(255) NOT NULL, 
	role VARCHAR(255) NOT NULL, 
	since_date DATE NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (process_code)
)

""")
    op.execute("""
CREATE TABLE hr_individual_development_plans (
	id SERIAL NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	goals JSON NOT NULL, 
	courses JSON NOT NULL, 
	review_date DATE, 
	status idpstatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE training_needs_assessments (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	role VARCHAR(255) NOT NULL, 
	skills_gap TEXT NOT NULL, 
	priority needpriority NOT NULL, 
	status needstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE tech_technical_specs (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	project_id INTEGER, 
	product VARCHAR(100), 
	version VARCHAR(10) NOT NULL, 
	content TEXT NOT NULL, 
	status specstatus NOT NULL, 
	approved_by VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_maintenance_records (
	id SERIAL NOT NULL, 
	asset VARCHAR(255) NOT NULL, 
	maintenance_type maintenancetype NOT NULL, 
	description TEXT NOT NULL, 
	scheduled_date DATE NOT NULL, 
	completed_date DATE, 
	performed_by VARCHAR(255), 
	status maintenancestatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_nps_surveys (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255) NOT NULL, 
	subscription_id INTEGER, 
	score INTEGER NOT NULL, 
	category npscategory NOT NULL, 
	feedback TEXT, 
	responded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_quality_policies (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	content TEXT NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	status policystatus NOT NULL, 
	approved_by VARCHAR(255), 
	approved_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_strategy_reviews (
	id SERIAL NOT NULL, 
	date DATE NOT NULL, 
	reviewed_by VARCHAR(255) NOT NULL, 
	summary TEXT NOT NULL, 
	decisions TEXT NOT NULL, 
	next_review_date DATE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE training_courses (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	modality coursemodality NOT NULL, 
	duration_hours INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	status coursestatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_job_descriptions (
	id SERIAL NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	department VARCHAR(255) NOT NULL, 
	reports_to VARCHAR(255), 
	responsibilities TEXT NOT NULL, 
	requirements TEXT NOT NULL, 
	competencies JSON NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE quality_audits (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	scheduled_date DATE NOT NULL, 
	audit_date DATE, 
	scope TEXT NOT NULL, 
	auditor VARCHAR(255) NOT NULL, 
	audited_process VARCHAR(3) NOT NULL, 
	status auditstatus NOT NULL, 
	result auditresult, 
	findings_summary TEXT, 
	report_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE tech_solution_sunsets (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	product VARCHAR(100) NOT NULL, 
	sunset_date DATE NOT NULL, 
	migration_path TEXT NOT NULL, 
	status sunsetstatus NOT NULL, 
	approved_by VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE quality_improvements (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	source_ref VARCHAR(50), 
	description TEXT NOT NULL, 
	expected_benefit TEXT, 
	responsible VARCHAR(255) NOT NULL, 
	status improvementstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	implemented_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE tech_risk_matrices (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	project_id INTEGER, 
	risks JSON NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE procurement_supplier_registrations (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	company_name VARCHAR(255) NOT NULL, 
	contact VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	services TEXT NOT NULL, 
	status supplierstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE tech_release_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	version VARCHAR(20) NOT NULL, 
	product VARCHAR(100) NOT NULL, 
	planned_date DATE NOT NULL, 
	actual_date DATE, 
	features JSON NOT NULL, 
	status releasestatus NOT NULL, 
	release_notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_csat_surveys (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255) NOT NULL, 
	project_id INTEGER, 
	score INTEGER NOT NULL, 
	feedback TEXT, 
	responded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_staff_register (
	id SERIAL NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	department VARCHAR(255) NOT NULL, 
	position VARCHAR(255) NOT NULL, 
	hire_date DATE NOT NULL, 
	contract_type hr_contract_type NOT NULL, 
	status staffstatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_management_reviews (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	review_period_start DATE NOT NULL, 
	review_period_end DATE NOT NULL, 
	prepared_by VARCHAR(255) NOT NULL, 
	summary TEXT NOT NULL, 
	conclusions JSON NOT NULL, 
	report_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_quality_objectives (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	objective TEXT NOT NULL, 
	process_code VARCHAR(3) NOT NULL, 
	target_value FLOAT NOT NULL, 
	actual_value FLOAT, 
	metric_unit VARCHAR(50) NOT NULL, 
	year INTEGER NOT NULL, 
	status objectivestatus NOT NULL, 
	responsible VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE procurement_purchase_requests (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	requester VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	quantity FLOAT NOT NULL, 
	estimated_cost FLOAT NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	justification TEXT NOT NULL, 
	status purchaserequeststatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_requests (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	requester VARCHAR(255) NOT NULL, 
	resource_type VARCHAR(20) NOT NULL, 
	specification TEXT NOT NULL, 
	justification TEXT NOT NULL, 
	status requeststatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_performance_evaluations (
	id SERIAL NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	evaluator VARCHAR(255) NOT NULL, 
	period VARCHAR(20) NOT NULL, 
	score INTEGER, 
	strengths TEXT, 
	improvements TEXT, 
	status evaluationstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE training_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	year INTEGER NOT NULL, 
	courses JSON NOT NULL, 
	budget NUMERIC(12, 2) NOT NULL, 
	status planstatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_satisfaction_reports (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	period VARCHAR(20) NOT NULL, 
	nps_score FLOAT, 
	csat_score FLOAT, 
	ces_score FLOAT, 
	complaints_count INTEGER, 
	response_rate FLOAT, 
	recommendations TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_ces_surveys (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255) NOT NULL, 
	subscription_id INTEGER, 
	score INTEGER NOT NULL, 
	task_description VARCHAR(500) NOT NULL, 
	responded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE commercial_icp_matrix (
	id SERIAL NOT NULL, 
	industry VARCHAR(255) NOT NULL, 
	company_size VARCHAR(100) NOT NULL, 
	role VARCHAR(255) NOT NULL, 
	pain_points TEXT NOT NULL, 
	fit_score INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE quality_documents (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	process_code VARCHAR(3) NOT NULL, 
	doc_type VARCHAR(10) NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	status documentstatus NOT NULL, 
	file_path VARCHAR(500), 
	approved_by VARCHAR(255), 
	approved_at TIMESTAMP WITH TIME ZONE, 
	next_review_at DATE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE training_competency_matrices (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	role VARCHAR(255) NOT NULL, 
	competencies JSON NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_incident_reports (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	service VARCHAR(255) NOT NULL, 
	severity incidentseverity NOT NULL, 
	description TEXT NOT NULL, 
	root_cause TEXT, 
	resolution TEXT, 
	status incidentstatus NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE strategic_marketing_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	year INTEGER NOT NULL, 
	goals TEXT NOT NULL, 
	budget NUMERIC(12, 2) NOT NULL, 
	activities JSON NOT NULL, 
	status marketingplanstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE tech_product_roadmaps (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	product_line productline NOT NULL, 
	year INTEGER NOT NULL, 
	vision TEXT NOT NULL, 
	strategic_goals TEXT NOT NULL, 
	items JSON NOT NULL, 
	status roadmapstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_continuity_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	last_reviewed DATE NOT NULL, 
	risk_assessment JSON NOT NULL, 
	recovery_strategies JSON NOT NULL, 
	status continuityplanstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE cx_exit_interviews (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	subscription_id INTEGER NOT NULL, 
	churn_reason_category churnreasoncategory NOT NULL, 
	detailed_feedback TEXT, 
	would_return BOOLEAN, 
	interview_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE hr_induction_checklists (
	id SERIAL NOT NULL, 
	employee_name VARCHAR(255) NOT NULL, 
	hire_date DATE NOT NULL, 
	items JSON NOT NULL, 
	status inductioncheckliststatus NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_availability_reports (
	id SERIAL NOT NULL, 
	service VARCHAR(255) NOT NULL, 
	period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
	uptime_percent FLOAT NOT NULL, 
	downtime_minutes INTEGER NOT NULL, 
	sla_met BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE infra_sla_agreements (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	provider VARCHAR(255) NOT NULL, 
	service VARCHAR(255) NOT NULL, 
	uptime_target FLOAT NOT NULL, 
	response_time_minutes INTEGER NOT NULL, 
	resolution_time_minutes INTEGER NOT NULL, 
	status slastatus NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE analytics_kpi_reports (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	period_start DATE NOT NULL, 
	period_end DATE NOT NULL, 
	indicators_data JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

""")
    op.execute("""
CREATE TABLE quality_corrective_actions (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	nc_id INTEGER NOT NULL, 
	description TEXT NOT NULL, 
	responsible VARCHAR(255) NOT NULL, 
	deadline DATE NOT NULL, 
	implementation_evidence TEXT, 
	effectiveness_review TEXT, 
	status actionstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(nc_id) REFERENCES quality_non_conformities (id)
)

""")
    op.execute("""
CREATE TABLE analytics_performance_data_records (
	id SERIAL NOT NULL, 
	indicator_id INTEGER NOT NULL, 
	period VARCHAR(7) NOT NULL, 
	value FLOAT NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	recorded_by VARCHAR(255) NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(indicator_id) REFERENCES analytics_performance_indicators (id)
)

""")
    op.execute("""
CREATE TABLE analytics_trend_analysis_reports (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	indicator_id INTEGER NOT NULL, 
	period_start DATE NOT NULL, 
	period_end DATE NOT NULL, 
	trend trenddirection NOT NULL, 
	change_percent FLOAT, 
	insights TEXT, 
	recommendations TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(indicator_id) REFERENCES analytics_performance_indicators (id)
)

""")
    op.execute("""
CREATE TABLE commercial_proposals (
	id SERIAL NOT NULL, 
	lead_id INTEGER NOT NULL, 
	version VARCHAR(10) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	lines JSON NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	valid_until DATE, 
	sent_at TIMESTAMP WITH TIME ZONE, 
	accepted_at TIMESTAMP WITH TIME ZONE, 
	rejection_reason TEXT, 
	created_by VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lead_id) REFERENCES commercial_leads (id)
)

""")
    op.execute("""
CREATE TABLE commercial_discoveries (
	id SERIAL NOT NULL, 
	lead_id INTEGER NOT NULL, 
	needs TEXT NOT NULL, 
	budget_range VARCHAR(255), 
	timeline VARCHAR(255), 
	decision_criteria TEXT, 
	pain_points TEXT, 
	recorded_by VARCHAR(255) NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (lead_id), 
	FOREIGN KEY(lead_id) REFERENCES commercial_leads (id)
)

""")
    op.execute("""
CREATE TABLE cx_complaint_register (
	id SERIAL NOT NULL, 
	complaint_id INTEGER NOT NULL, 
	registered_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	resolution_days INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (complaint_id), 
	FOREIGN KEY(complaint_id) REFERENCES cx_complaints (id)
)

""")
    op.execute("""
CREATE TABLE training_certification_records (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	participant_name VARCHAR(255) NOT NULL, 
	course_id INTEGER NOT NULL, 
	certificate_code VARCHAR(50) NOT NULL, 
	issued_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	expires_at DATE, 
	status certstatus NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(course_id) REFERENCES training_courses (id), 
	UNIQUE (certificate_code)
)

""")
    op.execute("""
CREATE TABLE training_sessions (
	id SERIAL NOT NULL, 
	course_id INTEGER NOT NULL, 
	instructor VARCHAR(255) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	attendees JSON NOT NULL, 
	status sessionstatus NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(course_id) REFERENCES training_courses (id)
)

""")
    op.execute("""
CREATE TABLE training_video_tutorials (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	course_id INTEGER, 
	url VARCHAR(500) NOT NULL, 
	duration_minutes INTEGER NOT NULL, 
	status videostatus NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(course_id) REFERENCES training_courses (id)
)

""")
    op.execute("""
CREATE TABLE quality_audit_checklist (
	id SERIAL NOT NULL, 
	audit_id INTEGER NOT NULL, 
	question TEXT NOT NULL, 
	result VARCHAR(20), 
	evidence TEXT, 
	nc_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(audit_id) REFERENCES quality_audits (id), 
	FOREIGN KEY(nc_id) REFERENCES quality_non_conformities (id)
)

""")
    op.execute("""
CREATE TABLE procurement_supplier_performance_reports (
	id SERIAL NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	period VARCHAR(20) NOT NULL, 
	avg_score FLOAT NOT NULL, 
	on_time_delivery_pct FLOAT NOT NULL, 
	quality_rating FLOAT NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(supplier_id) REFERENCES procurement_supplier_registrations (id)
)

""")
    op.execute("""
CREATE TABLE procurement_supplier_register (
	id SERIAL NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	approved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	approved_by VARCHAR(255) NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (supplier_id), 
	FOREIGN KEY(supplier_id) REFERENCES procurement_supplier_registrations (id)
)

""")
    op.execute("""
CREATE TABLE procurement_supplier_evaluations (
	id SERIAL NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	evaluator VARCHAR(255) NOT NULL, 
	criteria_scores JSON NOT NULL, 
	total_score FLOAT, 
	period VARCHAR(20) NOT NULL, 
	status proc_evaluation_status NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(supplier_id) REFERENCES procurement_supplier_registrations (id)
)

""")
    op.execute("""
CREATE TABLE tech_qa_test_reports (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	release_id INTEGER, 
	test_type testtype NOT NULL, 
	total_tests INTEGER NOT NULL, 
	passed INTEGER NOT NULL, 
	failed INTEGER NOT NULL, 
	blocked INTEGER NOT NULL, 
	report_url VARCHAR(500), 
	status reportstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES tech_release_plans (id)
)

""")
    op.execute("""
CREATE TABLE tech_uat_signoffs (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	release_id INTEGER, 
	project_id INTEGER, 
	signed_by VARCHAR(255) NOT NULL, 
	signed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	comments TEXT, 
	status uatstatus NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES tech_release_plans (id)
)

""")
    op.execute("""
CREATE TABLE tech_deployment_records (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	release_id INTEGER, 
	environment deploymentenvironment NOT NULL, 
	deployed_by VARCHAR(255) NOT NULL, 
	deployed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	rollback_at TIMESTAMP WITH TIME ZONE, 
	status deploymentstatus NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(release_id) REFERENCES tech_release_plans (id)
)

""")
    op.execute("""
CREATE TABLE procurement_receiving_reports (
	id SERIAL NOT NULL, 
	purchase_request_id INTEGER, 
	received_by VARCHAR(255) NOT NULL, 
	items JSON NOT NULL, 
	received_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	condition_ok BOOLEAN NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_request_id) REFERENCES procurement_purchase_requests (id)
)

""")
    op.execute("""
CREATE TABLE commercial_contracts (
	id SERIAL NOT NULL, 
	lead_id INTEGER NOT NULL, 
	proposal_id INTEGER, 
	contract_type contracttype NOT NULL, 
	contract_number VARCHAR(50) NOT NULL, 
	signed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE, 
	total_value NUMERIC(12, 2) NOT NULL, 
	monthly_value NUMERIC(10, 2), 
	sla_clauses TEXT, 
	status VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lead_id) REFERENCES commercial_leads (id), 
	FOREIGN KEY(proposal_id) REFERENCES commercial_proposals (id)
)

""")
    op.execute("""
CREATE TABLE training_attendance_records (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	participant_name VARCHAR(255) NOT NULL, 
	hours_attended FLOAT NOT NULL, 
	signed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id)
)

""")
    op.execute("""
CREATE TABLE training_evaluations (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	participant VARCHAR(255) NOT NULL, 
	score INTEGER NOT NULL, 
	feedback TEXT, 
	submitted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id)
)

""")
    op.execute("""
CREATE TABLE pmo_projects (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	contract_id INTEGER, 
	description TEXT, 
	product_line productline NOT NULL, 
	status projectstatus NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE, 
	budget NUMERIC(12, 2), 
	project_manager VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(contract_id) REFERENCES commercial_contracts (id)
)

""")
    op.execute("""
CREATE TABLE commercial_account_plans (
	id SERIAL NOT NULL, 
	contract_id INTEGER NOT NULL, 
	goals TEXT NOT NULL, 
	activities JSON NOT NULL, 
	review_date DATE, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(contract_id) REFERENCES commercial_contracts (id)
)

""")
    op.execute("""
CREATE TABLE commercial_subscriptions (
	id SERIAL NOT NULL, 
	contract_id INTEGER NOT NULL, 
	product VARCHAR(100) NOT NULL, 
	tier subscriptiontier NOT NULL, 
	status subscriptionstatus NOT NULL, 
	seats INTEGER NOT NULL, 
	activated_at TIMESTAMP WITH TIME ZONE, 
	churned_at TIMESTAMP WITH TIME ZONE, 
	churn_reason TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (contract_id), 
	FOREIGN KEY(contract_id) REFERENCES commercial_contracts (id)
)

""")
    op.execute("""
CREATE TABLE commercial_onboarding (
	id SERIAL NOT NULL, 
	contract_id INTEGER NOT NULL, 
	steps JSON NOT NULL, 
	status onboardingstatus NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (contract_id), 
	FOREIGN KEY(contract_id) REFERENCES commercial_contracts (id)
)

""")
    op.execute("""
CREATE TABLE pmo_closure_records (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	closed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	lessons_learned TEXT, 
	final_budget NUMERIC(12, 2), 
	customer_feedback TEXT, 
	status closurestatus NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_weekly_reports (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	week_number INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	accomplishments TEXT NOT NULL, 
	next_week_plan TEXT NOT NULL, 
	blockers TEXT, 
	status_percent INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_change_requests (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	description TEXT NOT NULL, 
	reason TEXT NOT NULL, 
	impact_analysis TEXT, 
	status crstatus NOT NULL, 
	requested_by VARCHAR(255) NOT NULL, 
	approved_by VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_execution_plans (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	phases JSON NOT NULL, 
	milestones JSON NOT NULL, 
	risks JSON NOT NULL, 
	status pmo_plan_status NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_handover_acceptances (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	accepted_by VARCHAR(255) NOT NULL, 
	accepted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	comments TEXT, 
	warranty_period_days INTEGER NOT NULL, 
	status handoverstatus NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_deliverables_checklists (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	items JSON NOT NULL, 
	status checkliststatus NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE pmo_follow_up_meetings (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	date DATE NOT NULL, 
	minutes TEXT NOT NULL, 
	action_items JSON NOT NULL, 
	next_meeting_date DATE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES pmo_projects (id)
)

""")
    op.execute("""
CREATE TABLE commercial_retention_actions (
	id SERIAL NOT NULL, 
	subscription_id INTEGER NOT NULL, 
	action_type VARCHAR(100) NOT NULL, 
	description TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	assigned_to VARCHAR(255) NOT NULL, 
	deadline DATE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subscription_id) REFERENCES commercial_subscriptions (id)
)

""")


def downgrade() -> None:
    op.execute("""DROP TABLE IF EXISTS commercial_retention_actions CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_follow_up_meetings CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_deliverables_checklists CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_handover_acceptances CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_execution_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_change_requests CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_weekly_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_closure_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_onboarding CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_subscriptions CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_account_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS pmo_projects CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_evaluations CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_attendance_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_contracts CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_receiving_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_deployment_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_uat_signoffs CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_qa_test_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_supplier_evaluations CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_supplier_register CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_supplier_performance_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_audit_checklist CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_video_tutorials CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_sessions CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_certification_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_complaint_register CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_discoveries CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_proposals CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS analytics_trend_analysis_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS analytics_performance_data_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_corrective_actions CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS analytics_kpi_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_sla_agreements CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_availability_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_induction_checklists CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_exit_interviews CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_continuity_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_product_roadmaps CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_marketing_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_incident_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_competency_matrices CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_documents CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_icp_matrix CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_ces_surveys CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_satisfaction_reports CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_performance_evaluations CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_requests CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_purchase_requests CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_quality_objectives CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_management_reviews CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_staff_register CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_csat_surveys CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_release_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS procurement_supplier_registrations CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_risk_matrices CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_improvements CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_solution_sunsets CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_audits CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_job_descriptions CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_courses CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_strategy_reviews CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_quality_policies CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_nps_surveys CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_maintenance_records CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS tech_technical_specs CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_needs_assessments CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_individual_development_plans CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_process_owners CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS cx_complaints CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS analytics_performance_dashboards CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS commercial_leads CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS analytics_performance_indicators CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS infra_security_incidents CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS strategic_qms_scope CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS training_user_manuals CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_personnel_requests CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS hr_labor_incidents CASCADE;""")
    op.execute("""DROP TABLE IF EXISTS quality_non_conformities CASCADE;""")

    op.execute("""DROP TYPE IF EXISTS videostatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS uatstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS trenddirection CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS testtype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS supplierstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS sunsetstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS subscriptiontier CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS subscriptionstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS staffstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS specstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS slastatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS sessionstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS securityincidenttype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS securityincidentstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS roadmapstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS requeststatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS reportstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS releasestatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS purchaserequeststatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS projectstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS productline CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS proc_evaluation_status CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS policystatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS pmo_plan_status CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS planstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS personnelrequeststatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS onboardingstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS objectivestatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS npscategory CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS needstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS needpriority CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS ncstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS ncseverity CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS marketingplanstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS manualstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS maintenancetype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS maintenancestatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS leadstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS inductioncheckliststatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS incidenttype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS incidentstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS incidentseverity CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS improvementstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS idpstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS hr_incident_status CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS hr_contract_type CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS handoverstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS frequency CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS evaluationstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS documentstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS deploymentstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS deploymentenvironment CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS crstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS coursestatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS coursemodality CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS contracttype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS continuityplanstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS complainttype CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS complaintstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS closurestatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS churnreasoncategory CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS checkliststatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS certstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS auditstatus CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS auditresult CASCADE;""")
    op.execute("""DROP TYPE IF EXISTS actionstatus CASCADE;""")

