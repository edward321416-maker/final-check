"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession } from "@/types/check";
import type { ExtractedRequirement, ExtractionStatus, ProfileRequirement, Modality, Severity, Verifier } from "@/types/profile";
import { useSession } from "./session-provider";
import { EvidenceBox, ErrorNotice, useAction } from "./ui";
import styles from "./profile.module.css";

export function TextAnnouncementInput() {
  const [text, setText] = useState("");
  const { update } = useSession();
  const router = useRouter();
  const { busy, error, run } = useAction();
  async function start() {
    const session = await request<CheckSession>("/sessions", { mode: "custom" });
    update(await sessionRequest(session.id, "announcement-text", { text, name: "직접 입력한 공고" }));
    router.push("/announcement");
  }
  return <div className={styles.form}><label>공고문 텍스트<textarea value={text} onChange={e => setText(e.target.value)} rows={6} maxLength={100000} disabled={busy} placeholder="제출방법과 파일 조건이 포함된 공고 원문을 붙여 넣으세요." /></label>
    <p>AI가 후보를 생성하고 별도 단계에서 검토합니다. 결과는 사람이 승인하기 전까지 공식 규칙이 아닙니다.</p>
    <p className="info-note">입력한 공고 내용은 이 PC의 ChatGPT 인증 Codex CLI를 통해 AI 요구사항 분석에 사용됩니다.</p>
    <div><button className="button secondary" disabled={busy || !text.trim()} onClick={() => void run(start)}>텍스트 공고로 시작 →</button></div><ErrorNotice error={error} /></div>;
}

export type ProfileReviewAction = "EDIT" | "NEEDS_REVIEW" | "APPROVE" | "DELETE";

const extractionStatusCopy = {
  EXTRACTED: "AI EXTRACTED",
  CONFIRMED: "HUMAN CONFIRMED",
  NEEDS_REVIEW: "NEEDS REVIEW",
  UNSUPPORTED: "UNSUPPORTED",
} as const satisfies Record<ExtractionStatus, string>;

export function formatExtractionStatus(status: ExtractionStatus): string {
  return extractionStatusCopy[status];
}

export function RequirementInspector({ item, busy, act, onDirty }: {
  item: ProfileRequirement;
  busy: boolean;
  onDirty: () => void;
  act: (id: string, action: ProfileReviewAction, requirement?: ExtractedRequirement) => void;
}) {
  const [draft, setDraft] = useState<ExtractedRequirement>(() => ({
    requirement_id: item.requirement_id, rule: item.rule, modality: item.modality, severity: item.severity,
    verifier: item.verifier, condition: item.condition, evidence: item.evidence, confidence: item.confidence,
  }));
  const set = <K extends keyof ExtractedRequirement>(key: K, value: ExtractedRequirement[K]) => {
    onDirty(); setDraft(old => ({ ...old, [key]: value }));
  };
  const reviewState = formatExtractionStatus(item.extraction_status);
  return <div>
    <div className={styles.actions}><span className="rule-id">{item.requirement_id}</span><strong>{reviewState}</strong><span className="verifier">confidence {item.confidence.toFixed(2)} · 미보정</span></div>
    <p className="info-note">Stage 2: {item.stage2_decision ?? "pending"} · {item.stage2_reason || "semantic review pending"}</p>
    {item.severity === "BLOCKER" && !item.authoritative && <p className="info-note"><strong>PROVISIONAL_BLOCKER</strong> · authoritative=false · 사람의 승인 전에는 제출을 차단하지 않습니다.</p>}
    <EvidenceBox label="공고문 근거" evidence={{ source: "입력 공고 원문", locator: `${item.evidence.source_section} · chars ${item.evidence_start}:${item.evidence_end}`, excerpt: item.evidence.quote }} />
    <div className={styles.form}><label>요구사항 문장<textarea rows={2} maxLength={2000} value={draft.rule} onChange={e => set("rule", e.target.value)} disabled={busy} /></label>
      <div className={styles.fields}>
        <label>modality<select value={draft.modality} onChange={e => set("modality", e.target.value as Modality)} disabled={busy}>{["MUST", "MUST_NOT", "SHOULD", "MAY", "INFO"].map(x => <option key={x}>{x}</option>)}</select></label>
        <label>severity<select value={draft.severity} onChange={e => set("severity", e.target.value as Severity)} disabled={busy}>{["BLOCKER", "REVIEW", "INFO", "EXTERNAL"].map(x => <option key={x}>{x}</option>)}</select></label>
        <label>verifier<select value={draft.verifier} onChange={e => set("verifier", e.target.value as Verifier)} disabled={busy}>{["DETERMINISTIC", "SEMANTIC", "VISION_SEMANTIC", "URL_CHECK", "EXTERNAL"].map(x => <option key={x}>{x}</option>)}</select></label>
      </div>
      <label>condition<input value={draft.condition} maxLength={1000} onChange={e => set("condition", e.target.value)} disabled={busy} /></label>
      <label>source section<input value={draft.evidence.source_section} maxLength={300} onChange={e => set("evidence", { ...draft.evidence, source_section: e.target.value })} disabled={busy} /></label>
      <label>exact evidence quote<textarea rows={2} maxLength={4000} value={draft.evidence.quote} onChange={e => set("evidence", { ...draft.evidence, quote: e.target.value })} disabled={busy} /></label>
    </div>
    {item.issues.map(issue => <p key={issue} className="info-note">{issue}</p>)}
    <div className={styles.actions}><button className="button secondary" disabled={busy} onClick={() => act(item.requirement_id, "EDIT", draft)}>수정 저장</button>
      <button className="button secondary" disabled={busy} onClick={() => act(item.requirement_id, "NEEDS_REVIEW", draft)}>검토 필요로 유지</button>
      <button className="button primary" disabled={busy} onClick={() => act(item.requirement_id, "APPROVE", draft)}>항목 승인</button>
      <button className="text-link" disabled={busy} onClick={() => act(item.requirement_id, "DELETE")}>항목 삭제</button></div>
  </div>;
}
