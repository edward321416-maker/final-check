import type { CheckSession } from "@/types/check";

export type WorkflowStep = "announcement" | "requirements" | "upload" | "results" | "recheck";

export interface WorkflowStepDefinition {
  key: WorkflowStep;
  href: string;
  label: string;
  number: string;
}

export const WORKFLOW_STEPS: readonly WorkflowStepDefinition[] = [
  { key: "announcement", href: "/announcement", label: "공고", number: "01" },
  { key: "requirements", href: "/requirements", label: "요구사항 검토", number: "02" },
  { key: "upload", href: "/upload", label: "제출파일", number: "03" },
  { key: "results", href: "/results", label: "결과", number: "04" },
  { key: "recheck", href: "/recheck", label: "재검사", number: "05" },
] as const;

function hasRequirementData(session: CheckSession): boolean {
  if (session.mode === "demo") {
    return session.validation_profile === "frozen_v15" && session.requirements.length > 0;
  }
  const profile = session.generic_profile;
  return Boolean(profile && ((profile.requirements?.length ?? 0) > 0 || profile.extraction_complete));
}

function canUpload(session: CheckSession): boolean {
  if (session.validation_profile === "frozen_v15") return true;
  return session.validation_profile === "generic" && session.generic_profile?.status === "CONFIRMED";
}

export function canEnterStep(session: CheckSession | null, step: WorkflowStep): boolean {
  if (!session?.announcement_name) return false;
  if (step === "announcement") return true;
  if (step === "requirements") return hasRequirementData(session);
  if (step === "upload") return canUpload(session);
  if (step === "results") return session.run_state === "COMPLETE" && session.results.length > 0;
  return session.results.length > 0 || session.previous_results.length > 0 || session.revision > 0;
}

export function isStepComplete(session: CheckSession | null, step: WorkflowStep): boolean {
  if (!session) return false;
  if (step === "announcement") return hasRequirementData(session);
  if (step === "requirements") return canUpload(session);
  if (step === "upload") return session.run_state === "COMPLETE" && session.results.length > 0;
  if (step === "results") return session.results.length > 0;
  return session.revision > 1;
}

export function recoveryHref(session: CheckSession | null, step: WorkflowStep): string {
  if (!session?.announcement_name) return "/";
  if (step === "requirements") return "/announcement";
  if (step === "upload") return session.mode === "custom" ? "/requirements" : "/announcement";
  if (step === "results") return canUpload(session) ? "/upload" : recoveryHref(session, "upload");
  if (step === "recheck") return session.results.length > 0 ? "/results" : recoveryHref(session, "results");
  return "/";
}
