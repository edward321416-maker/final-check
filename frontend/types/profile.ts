// Canonical API contract: backend/app/models/profiles.py.
export type Modality = "MUST" | "MUST_NOT" | "SHOULD" | "MAY" | "INFO";
export type Severity = "BLOCKER" | "REVIEW" | "INFO" | "EXTERNAL";
export type Verifier = "DETERMINISTIC" | "SEMANTIC" | "VISION_SEMANTIC" | "URL_CHECK" | "EXTERNAL";
export type ExtractionStatus = "EXTRACTED" | "NEEDS_REVIEW" | "CONFIRMED" | "UNSUPPORTED";
export type Stage2Decision = "KEEP" | "REVIEW" | "DROP";
export interface ProviderProvenance {
  provider: string; model: string | null; prompt_version: string; prompt_sha256: string;
  execution_kind: "ACTUAL" | "SIMULATED";
}
export interface ExtractedRequirement {
  requirement_id: string; rule: string; modality: Modality; severity: Severity; verifier: Verifier;
  condition: string; evidence: { source_section: string; quote: string }; confidence: number;
}
export interface ProfileRequirement extends ExtractedRequirement {
  extraction_status: ExtractionStatus; evidence_start: number; evidence_end: number;
  issues: string[]; original: ExtractedRequirement; stage1: ProviderProvenance | null;
  stage2_decision: "KEEP" | "REVIEW" | null; stage2_reason: string;
  stage2: ProviderProvenance | null; authoritative: boolean;
}
export interface GenericRequirementProfile {
  profile_type: "generic"; profile_id: string; status: "DRAFT" | "REVIEW_REQUIRED" | "CONFIRMED";
  announcement: { source_type: "TEXT" | "PDF"; name: string; sha256: string; text_sha256: string; text: string;
    ingestion_status: "READABLE" | "VISION_REQUIRED" | "UNREADABLE" | "UNSUPPORTED";
    page_count: number | null; notice: string };
  requirements: ProfileRequirement[]; raw_candidates: ExtractedRequirement[]; gated_candidate_ids: string[];
  stage2_reviews: { requirement_id: string; decision: Stage2Decision; reason: string; semantic_support: boolean;
    condition_preserved: boolean; modality_supported: boolean; needs_more_context: boolean;
    duplicate_of: string | null; reviewer: ProviderProvenance }[];
  provider: string | null; execution_kind: "ACTUAL" | "SIMULATED" | null;
  stage1: ProviderProvenance | null; stage2: ProviderProvenance | null;
  pipeline_status: "NOT_STARTED" | "RUNNING" | "COMPLETE" | "OVERFLOW_REVIEW" | "REVIEW_REQUIRED" | "EXTRACTION_ERROR";
  pipeline_error: string | null;
  raw_candidate_count: number; gated_candidate_count: number; dropped_candidate_count: number;
  review_batches: number; failed_batches: number[]; overflow: boolean; overflow_policy: string;
  extraction_complete: boolean; notices: string[];
  history: { action: string; requirement_id: string | null; at: string;
    before: ProfileRequirement | null; after: ProfileRequirement | null }[];
  version: number; created_at: string; updated_at: string;
}
