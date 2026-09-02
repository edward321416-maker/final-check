// API contract: backend/app/models/schemas.py. Verify with backend contract smoke.
export type FindingStatus = "BLOCKER" | "REVIEW" | "PASS" | "EXTERNAL";
export type SubmissionStatus = "NOT_CHECKED" | "BLOCKED" | "NEEDS_REVIEW" | "READY";
export interface Evidence { source: string; locator: string; excerpt: string }
export interface Requirement {
  id: string; title: string; description: string;
  verifier: "DETERMINISTIC" | "SEMANTIC" | "VISION" | "EXTERNAL";
  announcement_evidence: Evidence;
}
export interface ValidationResult {
  id: string; requirement_id: string; status: FindingStatus; title: string;
  explanation: string; action: string; announcement_evidence: Evidence | null;
  submission_evidence: Evidence | null; source_mode: "mock" | "validator";
}
export interface SubmissionFile { name: string; size_bytes: number; media_type: string; sha256: string }
export interface CheckSession {
  id: string; created_at: string; updated_at: string; mode: "demo" | "custom";
  source_mode: "mock" | "unavailable"; announcement_name: string | null;
  requirements: Requirement[]; files: SubmissionFile[]; results: ValidationResult[];
  previous_results: ValidationResult[]; status: SubmissionStatus; revision: number;
  fixture: "demo-broken" | "demo-fixed" | null;
}
