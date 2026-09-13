"use client";

import { useEffect, useRef } from "react";
import type { ValidationResult } from "@/types/check";
import { Badge, EvidenceBox, semanticAssessmentLabel, submissionEvidenceEmptyText } from "./ui";

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "a[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "summary",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

interface EvidenceDrawerProps {
  result: ValidationResult | null;
  opener: HTMLElement | null;
  onClose: () => void;
}

export function EvidenceDrawer({ result, opener, onClose }: EvidenceDrawerProps) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!result) return;
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusFrame = requestAnimationFrame(() => (closeRef.current ?? dialog).focus());

    function handleKeyDown(event: KeyboardEvent) {
      const activeDialog = dialogRef.current;
      if (!activeDialog) return;
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = Array.from(activeDialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
        .filter(element => !element.hasAttribute("disabled") && element.getAttribute("aria-hidden") !== "true");
      if (focusable.length === 0) {
        event.preventDefault();
        activeDialog.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && (active === first || !activeDialog.contains(active))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || !activeDialog.contains(active))) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      cancelAnimationFrame(focusFrame);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      opener?.focus();
    };
  }, [onClose, opener, result]);

  if (!result) return null;
  const semanticEvidence = result.semantic_review?.evidence.slice(0, 3) ?? [];
  const submissionEvidence = semanticEvidence[0] ?? result.submission_evidence;
  const assessment = semanticAssessmentLabel(result);

  return <div className="evidence-drawer-layer">
    <div className="evidence-drawer-backdrop" aria-hidden="true" />
    <section role="dialog" aria-modal="true" aria-label="Evidence Inspector" tabIndex={-1} ref={dialogRef} className="evidence-drawer">
      <header className="drawer-header">
        <div><span className="eyebrow">EVIDENCE INSPECTOR</span><h2>{result.title}</h2></div>
        <button ref={closeRef} type="button" className="drawer-close" aria-label="Evidence Inspector 닫기" onClick={onClose}>×</button>
      </header>
      <div className="drawer-body">
        <div className="drawer-status"><Badge status={result.status} />{assessment && <span>{assessment}</span>}</div>
        <EvidenceBox label="공고 요구사항" evidence={result.announcement_evidence} />
        <section className="drawer-evidence-group" aria-label="제출파일 근거">
          <EvidenceBox label="제출파일 근거" evidence={submissionEvidence} emptyText={submissionEvidenceEmptyText(result)} />
          {semanticEvidence.slice(1).map((evidence, index) => <EvidenceBox key={`${evidence.source}-${evidence.locator}-${index}`} label={`근거 후보 ${index + 2}`} evidence={evidence} />)}
        </section>
        <section className="drawer-explanation">
          <span className="evidence-label">{result.status === "REVIEW" ? "왜 REVIEW인가" : "판정 이유"}</span>
          <p>{result.explanation}</p>
          <div className="action-line"><span>다음 조치</span>{result.action}</div>
        </section>
        <details className="technical-details">
          <summary>기술 세부 보기</summary>
          <dl>
            <div><dt>requirement_id</dt><dd>{result.requirement_id}</dd></div>
            <div><dt>source_mode</dt><dd>{result.source_mode}</dd></div>
            {result.verification_plan_id && <div><dt>verification_plan_id</dt><dd>{result.verification_plan_id}</dd></div>}
            {result.checker_type && <div><dt>checker_type</dt><dd>{result.checker_type}</dd></div>}
            {result.semantic_review && <>
              <div><dt>semantic assessment</dt><dd>{result.semantic_review.assessment ?? "UNAVAILABLE"}</dd></div>
              <div><dt>semantic coverage</dt><dd>{result.semantic_review.coverage}</dd></div>
              {result.semantic_review.evidence_fingerprint && <div><dt>evidence_fingerprint</dt><dd>{result.semantic_review.evidence_fingerprint}</dd></div>}
              {result.semantic_review.reason_code && <div><dt>reason_code</dt><dd>{result.semantic_review.reason_code}</dd></div>}
              {result.semantic_review.provider && <>
                <div><dt>provider</dt><dd>{result.semantic_review.provider.provider}</dd></div>
                <div><dt>model</dt><dd>{result.semantic_review.provider.model ?? "not reported"}</dd></div>
                <div><dt>prompt_version</dt><dd>{result.semantic_review.provider.prompt_version}</dd></div>
                <div><dt>prompt_sha256</dt><dd>{result.semantic_review.provider.prompt_sha256}</dd></div>
                <div><dt>execution_kind</dt><dd>{result.semantic_review.provider.execution_kind}</dd></div>
              </>}
            </>}
          </dl>
        </details>
      </div>
    </section>
  </div>;
}
