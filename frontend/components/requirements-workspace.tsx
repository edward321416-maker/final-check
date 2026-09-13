"use client";

import Link from "next/link";
import { useState } from "react";
import { sessionRequest } from "@/lib/api";
import type { ExtractedRequirement } from "@/types/profile";
import { RequirementInspector, type ProfileReviewAction } from "./generic-profile";
import { splitEvidenceText } from "./announcement-workspace";
import { useSession } from "./session-provider";
import { ErrorNotice, EvidenceBox, useAction } from "./ui";
import styles from "./profile.module.css";

export function RequirementsWorkspace() {
  const { session, update } = useSession();
  const { busy, error, run } = useAction();
  const [acknowledged, setAcknowledged] = useState(false);
  const [dirtyId, setDirtyId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  if (!session) return null;

  if (session.mode === "demo") {
    return <div className="review-workspace">
      <section className="review-list" aria-label="동결 요구사항 목록"><div className="panel-heading"><h2>동결 공고 요구사항 · 읽기 전용</h2><span>읽기 전용</span></div>
        {session.requirements.map(rule => <article className="requirement" key={rule.id} aria-label={`요구사항 ${rule.id}`}><div className="requirement-summary"><span className="rule-id">{rule.id}</span><strong>{rule.title}</strong><span className="verifier">{rule.verifier}</span></div><EvidenceBox label="공고문 근거" evidence={rule.announcement_evidence} /></article>)}
      </section>
      <aside className="review-inspector" role="region" aria-label="요구사항 Inspector"><span className="eyebrow">HUMAN REVIEW</span><h2>Validator v1.5 · 이미 확정됨</h2><p>동결 Validator v1.5의 읽기 전용 요구사항입니다. 실시간 AI 추출 결과가 아닙니다.</p><Link href="/upload" className="button primary full">제출파일 선택하기 →</Link></aside>
    </div>;
  }

  const profile = session.generic_profile;
  if (!profile) return null;
  const selected = profile.requirements.find(item => item.requirement_id === selectedId) ?? profile.requirements[0] ?? null;
  const split = selected ? splitEvidenceText(profile.announcement.text, selected.evidence_start, selected.evidence_end, selected.evidence.quote) : null;
  const ready = profile.extraction_complete && profile.failed_batches.length === 0 && profile.requirements.length > 0
    && profile.requirements.every(item => item.extraction_status === "CONFIRMED" && item.authoritative);

  async function mutateRequirement(id: string, action: ProfileReviewAction, requirement?: ExtractedRequirement) {
    const next = await sessionRequest(session!.id, `requirements/${id}/review`, { expected_version: profile!.version, action, requirement });
    update(next);
    setAcknowledged(false);
    setDirtyId(null);
    if (action === "DELETE") setSelectedId(next.generic_profile?.requirements[0]?.requirement_id ?? null);
  }
  async function confirmProfile() {
    update(await sessionRequest(session!.id, "profile/confirm", { expected_version: profile!.version, reviewed_full_source: true }));
    setAcknowledged(false);
    setDirtyId(null);
  }
  async function compilePlan() {
    update(await sessionRequest(session!.id, "verification-plan/compile", { expected_version: profile!.version }));
  }

  return <div className="review-workspace">
    <section className="review-list" aria-label="요구사항 목록">
      <div className="panel-heading"><h2>Compact Review List</h2><span>{profile.requirements.length}개 항목</span></div>
      <div className={styles.notices}><p><strong>Profile: <span data-testid="profile-status">{profile.status}</span></strong></p><p>AI가 찾은 후보를 사람이 원문과 대조해 공식 요구사항으로 확정합니다.</p></div>
      {profile.requirements.map(item => <article className={`requirement requirement-row${selected?.requirement_id === item.requirement_id ? " selected" : ""}`} key={item.requirement_id} aria-label={`요구사항 ${item.requirement_id}`}>
        <button type="button" aria-label={`요구사항 ${item.requirement_id}`} disabled={dirtyId !== null && dirtyId !== item.requirement_id} onClick={() => setSelectedId(item.requirement_id)}>
          <span className="rule-id">{item.requirement_id}</span><strong>{item.rule}</strong><span className="verifier">{item.modality} · {item.verifier}</span><span className="candidate-state">{item.extraction_status === "CONFIRMED" ? "HUMAN CONFIRMED" : "AI EXTRACTED"}</span>
        </button>
      </article>)}
      <div className="profile-controls">
        <details><summary>공고 원문과 provenance</summary><p className={styles.provenance}>Profile ID: {profile.profile_id}<br />Source SHA-256: {profile.announcement.sha256}<br />Text SHA-256: {profile.announcement.text_sha256}<br />Stage1 prompt: {profile.stage1?.prompt_version ?? "pending"} · {profile.stage1?.prompt_sha256 ?? "pending"}<br />Stage2 prompt: {profile.stage2?.prompt_version ?? "pending"} · {profile.stage2?.prompt_sha256 ?? "pending"}<br />Version: {profile.version}</p></details>
        <details><summary>검토 이력 {profile.history.length}개</summary><ul className="checklist">{profile.history.map((event, index) => <li key={index}>{event.action} {event.requirement_id} · {event.at}</li>)}</ul></details>
        {profile.status !== "CONFIRMED" ? <><label className={styles.ack}><input type="checkbox" checked={acknowledged} disabled={busy} onChange={event => setAcknowledged(event.target.checked)} />공고 원문 전체와 누락 가능성을 직접 검토했습니다.</label><button className="button primary full" disabled={busy || dirtyId !== null || !ready || !acknowledged} onClick={() => void run(confirmProfile)}>Profile 확정</button></>
          : <><p className="info-note">HUMAN CONFIRMED · AI는 계획만 제안하며 판정 권한이 없습니다.</p><p className="info-note"><strong>Plan Gate: {session.verification_plan_state}</strong>{session.verification_plan_error ? ` · ${session.verification_plan_error}` : ""}</p>
            {session.verification_plan?.plans.length ? <section aria-label="자동 검사 계획 요약"><h3>자동 검사 계획</h3><ul className="checklist">{session.verification_plan.plans.map(plan => <li key={plan.plan_id}><strong>{plan.requirement_id} · {plan.status === "VERIFIED" ? "자동 검사 가능" : plan.status === "EXTERNAL" ? "외부 확인" : "검토 필요"}</strong><br />{plan.checker_type} · {plan.constraint.field} {plan.constraint.operator} {String(plan.constraint.value)} {plan.constraint.unit}<br /><small>공고 근거: {plan.parameter_provenance.source_substring}</small></li>)}</ul><p className={styles.provenance}>{session.verification_plan.planner_provenance.provider} · {session.verification_plan.planner_provenance.model}<br />{session.verification_plan.planner_provenance.prompt_version} · {session.verification_plan.planner_provenance.prompt_sha256}</p></section> : null}
            {session.verification_plan_state !== "READY" && <button className="button secondary full" disabled={busy} onClick={() => void run(compilePlan)}>자동 검사 계획 생성</button>}
            <p className="info-note">현재 MVP 자동 검사 지원: PDF / MP4. 자동 검사가 안전하지 않은 항목은 검토 필요로 남깁니다.</p>{dirtyId ? <p>수정 중인 항목을 먼저 저장하거나 승인하세요.</p> : <Link href="/upload" className="button primary full">제출파일 선택하기 →</Link>}</>}
        <ErrorNotice error={error} />
        <p><Link href="/" className="text-link">다른 공고로 새 검사</Link></p>
      </div>
    </section>
    <aside className="review-inspector" role="region" aria-label="요구사항 Inspector">
      <div className="panel-heading"><h2>요구사항 Inspector</h2><span>{selected?.requirement_id ?? "선택 없음"}</span></div>
      {selected ? <div className="workspace-body">
        <section className="inspector-source" role="region" aria-label="공고 원문"><h3>정확한 공고 근거</h3><pre className={styles.source}>{split ? <>{split.before}<mark className="source-highlight">{split.match}</mark>{split.after}</> : profile.announcement.text || "읽을 수 있는 텍스트 없음"}</pre>{!split && <div className="source-fallback"><strong>{selected.evidence.source_section}</strong><blockquote>{selected.evidence.quote}</blockquote></div>}</section>
        <RequirementInspector key={`${selected.requirement_id}:${profile.version}`} item={selected} busy={busy} onDirty={() => { setDirtyId(selected.requirement_id); setAcknowledged(false); }} act={(id, action, requirement) => void run(() => mutateRequirement(id, action, requirement))} />
      </div> : <div className="empty-inline"><h3>검토할 요구사항이 없습니다</h3><p>공고 단계에서 실제 요구사항 후보를 준비해 주세요.</p></div>}
    </aside>
  </div>;
}
