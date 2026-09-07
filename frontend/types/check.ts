// API contract: backend/app/models/schemas.py. Verify with backend contract smoke.
import type { GenericRequirementProfile, Verifier } from "./profile";
export type FindingStatus = "BLOCKER" | "REVIEW" | "PASS" | "EXTERNAL";
export type SubmissionStatus = "BLOCKED" | "REVIEW_REQUIRED" | "READY";
export interface Evidence { source: string; locator: string; excerpt: string }
export interface Requirement {
  id: string; title: string; description: string;
  verifier: Verifier | "VISION";
  announcement_evidence: Evidence;
}
export interface ValidationResult {
  id: string; requirement_id: string; status: FindingStatus; title: string;
  explanation: string; action: string; announcement_evidence: Evidence | null;
  submission_evidence: Evidence | null; source_mode: "validator" | "generic_review" | "generic_verifier";
  verification_plan_id: string | null; checker_type: CheckerType | null;
  measured_fact: string | null; expected_constraint: string | null;
}
export type CheckerType = "FILE_PRESENCE" | "FILE_COUNT" | "FILE_NAME" | "FILE_TYPE" | "FILE_SIZE" | "PDF_PAGE_COUNT" | "VIDEO_METADATA";
export interface VerificationPlan {
  plan_id: string; requirement_id: string; planner_disposition: "CANDIDATE" | "REVIEW_ONLY" | "EXTERNAL";
  checker_type: CheckerType; status: "VERIFIED" | "REVIEW_ONLY" | "EXTERNAL"; gate_reasons: string[];
  target_selector: { kind: "EXACT_NAME" | "UNIQUE_EXTENSION" | "ALL_BY_EXTENSION" | "ALL_FILES"; value: string | null };
  constraint: { field: string; operator: string; value: string | number; unit: string };
  parameter_provenance: { evidence_quote: string; evidence_start: number; evidence_end: number; source_substring: string; normalized_value: string | number; operator: string };
  planner_reason: string;
}
export interface VerificationPlanSet {
  plan_set_id: string; profile_id: string; profile_version: number; announcement_sha256: string;
  announcement_text_sha256: string; confirmed_requirements_sha256: string;
  planner_provenance: { provider: string; model: string; prompt_version: string; prompt_sha256: string; execution_kind: "ACTUAL" | "SIMULATED" };
  plan_schema_version: "task08-verification-plan-v1"; created_at: string; plans: VerificationPlan[];
}
export interface SubmissionFile { name: string; size_bytes: number; media_type: string; sha256: string }
export interface JobSummary {
  job_id: string; status: "PENDING" | "RUNNING" | "SUCCEEDED" | "RETRYABLE" | "FAILED";
  stage: "NOT_STARTED" | "STAGE1_COMPLETE" | "GATE_COMPLETE" | "STAGE2_BATCH_N_COMPLETE" | "FINALIZED";
  attempt: number; completed_stage2_batches: number[]; error_category: string | null; updated_at: string;
}
export interface CheckSession {
  id: string; created_at: string; updated_at: string; mode: "demo" | "custom";
  source_mode: "validator" | "generic_review" | "generic_verifier" | "unavailable"; announcement_name: string | null;
  validation_profile: "frozen_v15" | "generic" | null; engine_sha256: string | null;
  generic_profile: GenericRequirementProfile | null;
  verification_plan: VerificationPlanSet | null;
  verification_plan_state: "NOT_STARTED" | "RUNNING" | "READY" | "REVIEW_REQUIRED";
  verification_plan_error: string | null;
  current_job_id: string | null; current_job: JobSummary | null;
  run_state: "NOT_STARTED" | "RUNNING" | "COMPLETE" | "FAILED";
  validation_complete: boolean; run_error: string | null;
  requirements: Requirement[]; files: SubmissionFile[]; results: ValidationResult[];
  previous_results: ValidationResult[]; status: SubmissionStatus | null; revision: number;
  fixture: "demo-broken" | "demo-fixed" | null;
}
