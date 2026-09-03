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
  submission_evidence: Evidence | null; source_mode: "validator" | "generic_review";
}
export interface SubmissionFile { name: string; size_bytes: number; media_type: string; sha256: string }
export interface CheckSession {
  id: string; created_at: string; updated_at: string; mode: "demo" | "custom";
  source_mode: "validator" | "generic_review" | "unavailable"; announcement_name: string | null;
  validation_profile: "frozen_v15" | "generic" | null; engine_sha256: string | null;
  generic_profile: GenericRequirementProfile | null;
  run_state: "NOT_STARTED" | "RUNNING" | "COMPLETE" | "FAILED";
  validation_complete: boolean; run_error: string | null;
  requirements: Requirement[]; files: SubmissionFile[]; results: ValidationResult[];
  previous_results: ValidationResult[]; status: SubmissionStatus | null; revision: number;
  fixture: "demo-broken" | "demo-fixed" | null;
}
