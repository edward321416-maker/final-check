"use client";

import Link from "next/link";
import { useState } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession } from "@/types/check";
import type { ProfileRequirement } from "@/types/profile";
import { formatExtractionStatus } from "./generic-profile";
import { useSession } from "./session-provider";
import { ErrorNotice, EvidenceBox, useAction } from "./ui";
import styles from "./profile.module.css";

const jobStageCopy = {
  NOT_STARTED: "AI 요구사항 추출 준비",
  STAGE1_COMPLETE: "요구사항 후보 생성 완료",
  GATE_COMPLETE: "근거 게이트 완료",
  STAGE2_BATCH_N_COMPLETE: "의미 검토 배치 처리 중",
  FINALIZED: "검토 후보 준비 완료",
} as const;

export function splitEvidenceText(text: string, start: number, end: number, quote: string) {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > text.length) return null;
  const match = text.slice(start, end);
  if (match !== quote) return null;
  return { before: text.slice(0, start), match, after: text.slice(end) };
}

function ExactSource({ text, item }: { text: string; item: ProfileRequirement | null }) {
  const split = item ? splitEvidenceText(text, item.evidence_start, item.evidence_end, item.evidence.quote) : null;
  return <section className="source-pane" role="region" aria-label="공고 원문">
    <div className="panel-heading"><h2>Announcement Source</h2><span>{text.length.toLocaleString()} chars</span></div>
    <pre className={styles.source}>{split ? <>{split.before}<mark className="source-highlight">{split.match}</mark>{split.after}</> : text || "읽을 수 있는 텍스트 없음"}</pre>
    {item && !split && <div className="source-fallback"><strong>{item.evidence.source_section}</strong><blockquote>{item.evidence.quote}</blockquote></div>}
  </section>;
}

export function AnnouncementWorkspace() {
  const { session, update } = useSession();
  const { busy, error, run } = useAction();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  if (!session) return null;

  if (session.mode === "demo") {
    return <div className="extraction-workspace">
      <section className="source-pane" role="region" aria-label="동결 공고 요구사항">
        <div className="panel-heading"><h2>동결 공고 요구사항</h2><span>{session.requirements.length}개 항목</span></div>
        <div className="workspace-body"><p>Validator v1.5 예시입니다. 실시간 AI 추출 결과가 아닙니다.</p></div>
      </section>
      <section className="review-list" aria-label="Validator v1.5 요구사항">
        <div className="panel-heading"><h2>Validator v1.5 예시</h2><span>읽기 전용</span></div>
        {session.requirements.map(rule => <article className="requirement" key={rule.id} aria-label={`요구사항 ${rule.id}`}><div className="requirement-summary"><span className="rule-id">{rule.id}</span><strong>{rule.title}</strong><span className="verifier">{rule.verifier}</span></div><p>{rule.description}</p><EvidenceBox label="공고문 근거" evidence={rule.announcement_evidence} /></article>)}
        <div className="workspace-actions"><Link href="/requirements" className="button primary">요구사항 검토로 이동 →</Link></div>
      </section>
    </div>;
  }

  const profile = session.generic_profile;
  if (!profile) return null;
  const selected = profile.requirements.find(item => item.requirement_id === selectedId) ?? profile.requirements[0] ?? null;
  async function extractAndWait() {
    let next = await sessionRequest(session!.id, "extract", { expected_version: profile!.version });
    update(next);
    while (next.generic_profile?.pipeline_status === "RUNNING") {
      await new Promise(resolve => setTimeout(resolve, 1000));
      next = await request<CheckSession>(`/sessions/${session!.id}`);
      update(next);
    }
  }
  const activity = session.current_job ? jobStageCopy[session.current_job.stage]
    : profile.pipeline_status === "RUNNING" ? "AI 요구사항 추출 준비"
    : profile.extraction_complete ? "검토 후보 준비 완료" : "AI 요구사항 추출 준비";

  return <>
    <div className="workspace-status">
      <p><strong>Profile: <span data-testid="profile-status">{profile.status}</span></strong> · {profile.announcement.ingestion_status}</p>
      <p>{profile.execution_kind ?? "아직 실행 전"} · {profile.provider ?? "Two-stage provider 대기 중"}</p>
      <p><strong>{activity}</strong> · {profile.pipeline_status}</p>
      <p>RAW {profile.raw_candidate_count} · GATED {profile.gated_candidate_count} · DROP {profile.dropped_candidate_count} · Stage2 batch {profile.review_batches}</p>
      {session.current_job && <p>Job {session.current_job.status} · attempt {session.current_job.attempt}/3 · completed batches {session.current_job.completed_stage2_batches.length}</p>}
      {profile.pipeline_error && <p className="info-note"><strong>Provider status:</strong> {profile.pipeline_error}</p>}
      {profile.overflow && <p className="info-note"><strong>OVERFLOW_REVIEW</strong> · 100개를 초과해도 전체를 버리지 않습니다. {profile.overflow_policy}</p>}
      {profile.failed_batches.length > 0 && <p className="info-note">실패 batch: {profile.failed_batches.map(i => i + 1).join(", ")} · 성공한 결과는 보존됐습니다.</p>}
      <p>{profile.announcement.notice}</p>
      {profile.notices.map((notice, index) => <p key={index}>{notice}</p>)}
      {!profile.extraction_complete && profile.pipeline_status !== "RUNNING" && profile.announcement.ingestion_status === "READABLE" && session.current_job?.status !== "FAILED" && <button className="button primary" disabled={busy} onClick={() => void run(extractAndWait)}>{profile.pipeline_status === "NOT_STARTED" ? "요구사항 추출 실행" : "저장된 단계부터 다시 실행"}</button>}
      {session.current_job?.status === "FAILED" && <p className="info-note">재시도 한도에 도달했습니다. 새 공고 profile로 다시 시작하세요.</p>}
      {profile.announcement.ingestion_status !== "READABLE" && <p className="info-note">요구사항 0개 · VISION_REQUIRED 또는 읽을 수 있는 공고 원문이 필요합니다. 내용을 생성하지 않았습니다.</p>}
      <ErrorNotice error={error} />
    </div>
    <div className="extraction-workspace">
      <ExactSource text={profile.announcement.text} item={selected} />
      <section className="review-list" aria-label="AI 추출 후보">
        <div className="panel-heading"><h2>{profile.requirements.length > 0 ? "Extracted Requirements" : "요구사항 검토 준비"}</h2><span>{profile.requirements.length}개 후보</span></div>
        {profile.requirements.map(item => <article className={`requirement requirement-candidate${selected?.requirement_id === item.requirement_id ? " selected" : ""}`} key={item.requirement_id} aria-label={`요구사항 ${item.requirement_id}`}>
          <button type="button" aria-label={`요구사항 ${item.requirement_id}`} onClick={() => setSelectedId(item.requirement_id)} onFocus={() => setSelectedId(item.requirement_id)}>
            <span className="rule-id">{item.requirement_id}</span><strong>{item.rule}</strong><span className="verifier">{item.modality} · {item.verifier}</span><span className="candidate-state">{formatExtractionStatus(item.extraction_status)}</span>
          </button>
        </article>)}
        {profile.extraction_complete && profile.requirements.length > 0 && <div className="workspace-actions"><p>AI 후보는 아직 공식 규칙이 아닙니다. 다음 단계에서 원문과 대조해 승인합니다.</p><Link href="/requirements" className="button primary">요구사항 검토로 이동 →</Link></div>}
      </section>
    </div>
  </>;
}
