"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession } from "@/types/check";
import type { ExtractedRequirement, ProfileRequirement, Modality, Severity, Verifier } from "@/types/profile";
import { useSession } from "./session-provider";
import { ErrorNotice, EvidenceBox, useAction } from "./ui";
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
    <p>ACTUAL LOCAL AI PROVIDER · AI가 후보를 생성하고 별도 단계에서 검토합니다. 결과는 사람이 승인하기 전까지 공식 규칙이 아닙니다.</p>
    <div><button className="button secondary" disabled={busy || !text.trim()} onClick={() => void run(start)}>텍스트 공고로 시작 →</button></div><ErrorNotice error={error} /></div>;
}

type Action = "EDIT" | "NEEDS_REVIEW" | "APPROVE" | "DELETE";
function ReviewCard({ item, busy, act, onDirty }: { item: ProfileRequirement; busy: boolean; onDirty: () => void;
  act: (id: string, action: Action, requirement?: ExtractedRequirement) => void }) {
  const [draft, setDraft] = useState<ExtractedRequirement>(() => ({
    requirement_id: item.requirement_id, rule: item.rule, modality: item.modality, severity: item.severity,
    verifier: item.verifier, condition: item.condition, evidence: item.evidence, confidence: item.confidence,
  }));
  const set = <K extends keyof ExtractedRequirement>(key: K, value: ExtractedRequirement[K]) => {
    onDirty(); setDraft(old => ({ ...old, [key]: value }));
  };
  const reviewState = item.extraction_status === "CONFIRMED" ? "Human Confirmed"
    : item.extraction_status === "NEEDS_REVIEW" ? "Needs Review"
    : item.stage2_decision === "KEEP" ? "AI reviewed · human approval required"
    : "Needs Review";
  return <article className="requirement" aria-label={`요구사항 ${item.requirement_id}`}>
    <div className={styles.actions}><span className="rule-id">{item.requirement_id}</span><strong>{reviewState}</strong><span className="verifier">AI generated · confidence {item.confidence.toFixed(2)} · 미보정</span></div>
    <p className="info-note">Stage 2: {item.stage2_decision ?? "pending"} · {item.stage2_reason || "semantic review pending"}</p>
    {item.severity === "BLOCKER" && !item.authoritative && <p className="info-note"><strong>PROVISIONAL_BLOCKER</strong> · authoritative=false · 사람의 승인 전에는 제출을 차단하지 않습니다.</p>}
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
    <EvidenceBox label="공고문 근거" evidence={{ source: "입력 공고 원문", locator: `${item.evidence.source_section} · chars ${item.evidence_start}:${item.evidence_end}`, excerpt: item.evidence.quote }} />
    {item.issues.map(issue => <p key={issue} className="info-note">{issue}</p>)}
    <div className={styles.actions}><button className="button secondary" disabled={busy} onClick={() => act(item.requirement_id, "EDIT", draft)}>수정 저장</button>
      <button className="button secondary" disabled={busy} onClick={() => act(item.requirement_id, "NEEDS_REVIEW", draft)}>검토 필요로 유지</button>
      <button className="button primary" disabled={busy} onClick={() => act(item.requirement_id, "APPROVE", draft)}>항목 승인</button>
      <button className="text-link" disabled={busy} onClick={() => act(item.requirement_id, "DELETE")}>항목 삭제</button></div>
  </article>;
}

export function GenericProfileReview() {
  const { session, update } = useSession();
  const { busy, error, run } = useAction();
  const [acknowledged, setAcknowledged] = useState(false);
  const [dirtyId, setDirtyId] = useState<string | null>(null);
  const profile = session?.generic_profile;
  if (!session || !profile) return null;
  const sid = session.id;
  async function mutate(action: string, body: object = {}) {
    update(await sessionRequest(sid, action, { ...body, expected_version: profile!.version }));
    setAcknowledged(false);
    setDirtyId(null);
  }
  async function extractAndWait() {
    let next = await sessionRequest(sid, "extract", { expected_version: profile!.version });
    update(next);
    while (next.generic_profile?.pipeline_status === "RUNNING") {
      await new Promise(resolve => setTimeout(resolve, 1000));
      next = await request<CheckSession>(`/sessions/${sid}`);
      update(next);
    }
    setAcknowledged(false);
    setDirtyId(null);
  }
  const ready = profile.extraction_complete && profile.failed_batches.length === 0 && profile.requirements.length > 0
    && profile.requirements.every(item => item.extraction_status === "CONFIRMED" && item.authoritative);
  return <div className="content-grid"><section className="panel"><div className="panel-heading"><h2>요구사항 검토</h2><span>{profile.requirements.length}개 항목</span></div>
    <div className={styles.notices}>
      <p><strong>Profile: <span data-testid="profile-status">{profile.status}</span></strong> · {profile.announcement.ingestion_status}</p>
      <p>{profile.execution_kind ?? "아직 실행 전"} · {profile.provider ?? "Two-stage provider 대기 중"}</p>
      <p><strong>Pipeline: {profile.pipeline_status}</strong> · RAW {profile.raw_candidate_count} · GATED {profile.gated_candidate_count} · DROP {profile.dropped_candidate_count} · Stage2 batch {profile.review_batches}</p>
      {profile.pipeline_status === "RUNNING" && <p className="info-note">실제 AI 추출을 실행 중입니다. 완료 상태를 자동으로 확인합니다.</p>}
      {profile.pipeline_error && <p className="info-note"><strong>Provider status:</strong> {profile.pipeline_error}</p>}
      {profile.overflow && <p className="info-note"><strong>OVERFLOW_REVIEW</strong> · 100개를 초과해도 전체를 버리지 않습니다. {profile.overflow_policy}</p>}
      {profile.failed_batches.length > 0 && <p className="info-note">실패 batch: {profile.failed_batches.map(i => i + 1).join(", ")} · 성공한 결과는 보존됐습니다.</p>}
      <p>{profile.announcement.notice}</p>
      {profile.notices.map((notice, i) => <p key={i}>{notice}</p>)}
      {!profile.extraction_complete && profile.pipeline_status !== "RUNNING" && profile.announcement.ingestion_status === "READABLE" && <button className="button primary" disabled={busy} onClick={() => void run(extractAndWait)}>{profile.pipeline_status === "NOT_STARTED" ? "요구사항 추출 실행" : "실패 단계 다시 실행"}</button>}
      {profile.announcement.ingestion_status !== "READABLE" && <p className="info-note">요구사항 0개 · Vision 또는 읽을 수 있는 공고 원문이 필요합니다. 내용을 생성하지 않았습니다.</p>}
      <ErrorNotice error={error} />
    </div>
    {profile.requirements.map(item => <ReviewCard key={`${item.requirement_id}:${profile.version}`} item={item} busy={busy || (dirtyId !== null && dirtyId !== item.requirement_id)}
      onDirty={() => { setDirtyId(item.requirement_id); setAcknowledged(false); }}
      act={(id, action, requirement) => void run(() => mutate(`requirements/${id}/review`, { action, requirement }))} />)}
  </section><aside className="side-panel"><span className="eyebrow">ANNOUNCEMENT / HUMAN REVIEW</span><h3>{profile.announcement.name}</h3>
    <p>추출 후보를 원문과 대조해 수정·삭제·승인하세요. 항목 승인은 제출파일이 조건을 충족했다는 뜻이 아닙니다.</p>
    <details><summary>공고 원문과 provenance</summary><pre className={styles.source}>{profile.announcement.text || "읽을 수 있는 텍스트 없음"}</pre>
      <p className={styles.provenance}>Profile ID: {profile.profile_id}<br />Source SHA-256: {profile.announcement.sha256}<br />Text SHA-256: {profile.announcement.text_sha256}<br />Stage1 prompt: {profile.stage1?.prompt_version ?? "pending"} · {profile.stage1?.prompt_sha256 ?? "pending"}<br />Stage2 prompt: {profile.stage2?.prompt_version ?? "pending"} · {profile.stage2?.prompt_sha256 ?? "pending"}<br />Version: {profile.version}</p></details>
    <details><summary>검토 이력 {profile.history.length}개</summary><ul className="checklist">{profile.history.map((event, i) => <li key={i}>{event.action} {event.requirement_id} · {event.at}</li>)}</ul></details>
    {profile.status !== "CONFIRMED" ? <><label className={styles.ack}><input type="checkbox" checked={acknowledged} disabled={busy} onChange={e => setAcknowledged(e.target.checked)} />공고 원문 전체와 누락 가능성을 직접 검토했습니다.</label>
      <button className="button primary full" disabled={busy || dirtyId !== null || !ready || !acknowledged} onClick={() => void run(() => mutate("profile/confirm", { reviewed_full_source: true }))}>Profile 확정</button></>
      : <><p className="info-note">Human Confirmed · 확인된 requirement profile만 검증 파이프라인에 전달합니다. Generic 자동 검증은 미지원이므로 REVIEW / EXTERNAL만 표시합니다.</p>{dirtyId ? <p>수정 중인 항목을 먼저 저장하거나 승인하세요.</p> : <Link href="/upload" className="button primary full">제출파일 선택하기 →</Link>}</>}
    <p><Link href="/" className="text-link">다른 공고로 새 검사</Link></p>
  </aside></div>;
}
