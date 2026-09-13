"use client";

import Link from "next/link";
import { useCallback, useState, type MouseEvent } from "react";
import type { CheckSession, FindingStatus, ValidationResult } from "@/types/check";
import { EvidenceDrawer } from "./evidence-drawer";
import { Badge, EvidenceBox, semanticAssessmentLabel, submissionEvidenceEmptyText } from "./ui";

export const STATUS_PRIORITY: Record<FindingStatus, number> = { BLOCKER: 0, REVIEW: 1, PASS: 2, EXTERNAL: 3 };
const STATUSES: FindingStatus[] = ["BLOCKER", "REVIEW", "PASS", "EXTERNAL"];

function resultChanged(oldResult: ValidationResult, current: ValidationResult) {
  if (oldResult.status !== current.status) return true;
  return oldResult.semantic_review?.evidence_fingerprint !== current.semantic_review?.evidence_fingerprint
    || oldResult.semantic_review?.assessment !== current.semantic_review?.assessment
    || oldResult.semantic_review?.reason_code !== current.semantic_review?.reason_code;
}

function semanticState(result: ValidationResult) {
  if (result.semantic_review?.assessment === "NO_CLEAR_EVIDENCE") return "명확한 근거 후보 미발견";
  if (result.semantic_review?.assessment === "RELATED_EVIDENCE_FOUND") {
    const locator = result.semantic_review.evidence[0]?.locator ?? result.submission_evidence?.locator ?? "제출물";
    return `${locator} 관련 근거 후보 발견`;
  }
  return "내용 근거 확인 필요";
}

function EvidenceChainCard({ result, onInspect }: { result: ValidationResult; onInspect: (result: ValidationResult, opener: HTMLElement) => void }) {
  const semanticEvidence = result.semantic_review?.evidence.slice(0, 3) ?? [];
  const submissionEvidence = semanticEvidence[0] ?? result.submission_evidence;
  const assessment = semanticAssessmentLabel(result);
  const openInspector = (event: MouseEvent<HTMLButtonElement>) => onInspect(result, event.currentTarget);
  return <article data-testid="result-card" className={`result-card status-${result.status.toLowerCase()}`} aria-label={`${result.requirement_id} ${result.title}`}>
    <section className="evidence-chain-zone rule-zone">
      <span className="chain-label">RULE</span>
      <span className="rule-id">{result.requirement_id}</span>
      <h3>{result.title}</h3>
      {result.expected_constraint && <p className="constraint"><span>기대 조건</span><code>{result.expected_constraint}</code></p>}
    </section>
    <section className="evidence-chain-zone evidence-zone">
      <span className="chain-label">EVIDENCE</span><span className="evidence-trace" aria-hidden="true">→</span>
      {result.measured_fact && <p className="measured-fact"><span>실제 측정</span><code>{result.measured_fact}</code></p>}
      <div className="evidence-grid">
        <EvidenceBox label="공고문 근거" evidence={result.announcement_evidence} />
        <EvidenceBox label="제출파일 근거" evidence={submissionEvidence} emptyText={submissionEvidenceEmptyText(result)} />
      </div>
      {semanticEvidence.length > 1 && <section className="semantic-evidence"><span className="evidence-label">추가 근거 후보</span>{semanticEvidence.slice(1).map((evidence, index) => <EvidenceBox key={`${evidence.source}-${evidence.locator}-${index}`} label={`근거 후보 ${index + 2}`} evidence={evidence} />)}</section>}
    </section>
    <section className="evidence-chain-zone verdict-zone">
      <span className="chain-label">VERDICT</span>
      <Badge status={result.status} />
      {assessment && <p className="assessment-label">{assessment}</p>}
      <p>{result.explanation}</p>
      <div className="action-line"><span>다음 조치</span>{result.action}</div>
      <button type="button" className="button secondary evidence-button" onClick={openInspector} aria-label={`${result.requirement_id} ${result.title} 근거 자세히 보기`}>근거 자세히 보기</button>
    </section>
  </article>;
}

export function ResultsWorkspace({ session }: { session: CheckSession }) {
  const [filter, setFilter] = useState<FindingStatus | "ALL">("ALL");
  const [selectedResult, setSelectedResult] = useState<ValidationResult | null>(null);
  const [drawerOpener, setDrawerOpener] = useState<HTMLElement | null>(null);
  const results = [...session.results].sort((a, b) => STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]);
  const counts = Object.fromEntries(STATUSES.map(status => [status, results.filter(result => result.status === status).length])) as Record<FindingStatus, number>;
  const blockers = counts.BLOCKER;
  const previous = session.previous_results;
  const changes = results.flatMap(result => {
    const old = previous.find(item => item.requirement_id === result.requirement_id);
    return old && resultChanged(old, result) ? [{ old, result }] : [];
  });
  const statusChanges = changes.filter(({ old, result }) => old.status !== result.status);
  const visibleResults = results.filter(result => filter === "ALL" || result.status === filter);
  const title = blockers ? "제출 전, 수정이 필요합니다" : session.status === "READY" ? "자동 확인 가능한 필수 조건을 충족했습니다." : previous.some(result => result.status === "BLOCKER") ? "수정 완료. 직접 확인할 항목이 남았어요" : "직접 확인할 항목이 남았어요";
  const openInspector = useCallback((result: ValidationResult, opener: HTMLElement) => {
    setDrawerOpener(opener);
    setSelectedResult(result);
  }, []);
  const closeInspector = useCallback(() => setSelectedResult(null), []);

  return <>
    <section className={`result-banner ${blockers ? "has-blocker" : ""}`} aria-label="전체 검사 상태">
      <div className="result-title"><span className="alert-symbol">{blockers ? "!" : "↗"}</span><div><span className="eyebrow">{session.status} · CHECK {String(session.revision).padStart(2, "0")}</span><h2>{title}</h2><p>{blockers ? `BLOCKER ${blockers}개를 수정한 후 재검사하세요.` : "자동 확인 가능한 필수 조건의 결과와 남아 있는 REVIEW 항목을 함께 확인하세요."}</p></div></div>
      <div className="result-summary-counts" aria-label="판정 요약">{STATUSES.map(status => <span key={status}><b>{counts[status]}</b>{status}</span>)}</div>
      <Link className="button primary" href="/recheck">수정 후 재검사 →</Link>
    </section>
    {previous.length > 0 && <section className="comparison" aria-label="재검사 비교"><strong>이전 검사와 비교</strong><span>{statusChanges.length}개 판정 변경</span>{changes.map(({ old, result }) => old.status !== result.status ? <span className="change" key={result.id}>{result.requirement_id} <Badge status={old.status} /><span>→</span><Badge status={result.status} /></span> : <span className="change" key={result.id}>{result.requirement_id} 내용 근거 상태가 변경되었습니다.<br />이전: {semanticState(old)}<br />현재: {semanticState(result)}</span>)}{changes.length === 0 && <span>변경된 판정이 없습니다.</span>}</section>}
    <div className="results-heading"><div className="filter-tabs" role="group" aria-label="판정 필터"><button type="button" aria-pressed={filter === "ALL"} onClick={() => setFilter("ALL")}>전체 <b>{results.length}</b></button>{STATUSES.map(status => <button type="button" key={status} aria-pressed={filter === status} onClick={() => setFilter(status)}>{status} <b>{counts[status]}</b></button>)}</div><span className="muted">{session.validation_profile === "generic" ? "Generic Profile · 확인된 계획의 코드 검사" : "근거 기반 검사 결과 · v1.5"}</span></div>
    <section className="findings" aria-label="검사 결과 목록">{visibleResults.map(result => <EvidenceChainCard key={result.id} result={result} onInspect={openInspector} />)}
      {visibleResults.length === 0 && <div className="empty-inline">이 상태의 판정은 없습니다.</div>}
    </section>
    <div className="results-footer"><span>{session.validation_profile === "generic" ? "사람이 확정한 요구사항과 게이트를 통과한 계획만 코드로 검사했습니다. REVIEW / EXTERNAL은 직접 확인하세요." : "원본 Validator v1.5의 실제 검사 결과입니다. REVIEW 항목과 최종 제출은 직접 확인하세요."}</span><Link href="/recheck" className="text-link">수정 패키지 재검사 →</Link></div>
    <EvidenceDrawer result={selectedResult} opener={drawerOpener} onClose={closeInspector} />
  </>;
}
