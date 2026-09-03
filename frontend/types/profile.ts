// Canonical API contract: backend/app/models/profiles.py.
export type Modality = "MUST" | "MUST_NOT" | "SHOULD" | "MAY" | "INFO";
export type Severity = "BLOCKER" | "REVIEW" | "INFO" | "EXTERNAL";
export type Verifier = "DETERMINISTIC" | "SEMANTIC" | "VISION_SEMANTIC" | "URL_CHECK" | "EXTERNAL";
export type ExtractionStatus = "EXTRACTED" | "NEEDS_REVIEW" | "CONFIRMED" | "UNSUPPORTED";
export interface ExtractedRequirement {
  requirement_id: string; rule: string; modality: Modality; severity: Severity; verifier: Verifier;
  condition: string; evidence: { source_section: string; quote: string }; confidence: number;
}
export interface ProfileRequirement extends ExtractedRequirement {
  extraction_status: ExtractionStatus; evidence_start: number; evidence_end: number;
  issues: string[]; original: ExtractedRequirement;
}
export interface GenericRequirementProfile {
  profile_type: "generic"; profile_id: string; status: "DRAFT" | "REVIEW_REQUIRED" | "CONFIRMED";
  announcement: { source_type: "TEXT" | "PDF"; name: string; sha256: string; text_sha256: string; text: string;
    ingestion_status: "READABLE" | "VISION_REQUIRED" | "UNREADABLE" | "UNSUPPORTED";
    page_count: number | null; notice: string };
  requirements: ProfileRequirement[]; provider: string | null; execution_kind: "ACTUAL" | "SIMULATED" | null;
  extraction_complete: boolean; notices: string[];
  history: { action: string; requirement_id: string | null; at: string;
    before: ProfileRequirement | null; after: ProfileRequirement | null }[];
  version: number; created_at: string; updated_at: string;
}
