"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { request, sessionRequest } from "@/lib/api";
import { pollSession } from "@/lib/poll-session";
import type { CheckSession, FindingStatus, SemanticReadiness, SubmissionFile, ValidationResult } from "@/types/check";
import { useSession } from "./session-provider";
import { Badge, EvidenceBox, ModeNote, PageTitle, useAction, WorkflowGuard } from "./ui";
import { AnnouncementWorkspace } from "./announcement-workspace";
import { RequirementsWorkspace } from "./requirements-workspace";
import { LandingScreen } from "./landing";
import { PreflightPackageWorkspace } from "./preflight-package";

export function HomeScreen() {
  return <LandingScreen />;
}

export function AnnouncementScreen() {
  return <WorkflowGuard step="announcement"><ModeNote /><PageTitle step="01 / ANNOUNCEMENT ANALYSIS" title="공고의 조건부터 확인하세요" description="제출 전에 지켜야 할 조건과 공고문에 적힌 근거를 살펴봅니다." />
    <AnnouncementWorkspace />
  </WorkflowGuard>;
}

export function RequirementsScreen() {
  return <WorkflowGuard step="requirements"><ModeNote /><PageTitle step="02 / REQUIREMENTS REVIEW" title="확정 전 요구사항을 확인하세요" description="공고에서 확인된 요구사항과 원문 근거를 읽고 다음 검사 범위를 확인합니다." />
    <RequirementsWorkspace />
  </WorkflowGuard>;
}

export function UploadScreen({ recheck = false }: { recheck?: boolean }) {
  const { session, update } = useSession();
  const router = useRouter();
  const { busy, error, run } = useAction();
  const [selected, setSelected] = useState<File[]>([]);
  const [readiness, setReadiness] = useState<SemanticReadiness | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [pollError, setPollError] = useState("");
  const activeSessionId = useRef(session?.id);
  activeSessionId.current = session?.id;
  const pollingGeneration = useRef(0);
  const pollingSession = useRef<{ id: string; generation: number; controller: AbortController } | null>(null);
  async function loadReadiness(current: CheckSession) {
    setAcknowledged(false);
    setReadiness(null);
    setReadiness(await request<SemanticReadiness>(`/sessions/${current.id}/semantic-readiness`));
  }
  async function resumePolling(current: CheckSession) {
    if (pollingSession.current?.id === current.id) return;
    pollingSession.current?.controller.abort();
    const generation = pollingGeneration.current + 1;
    pollingGeneration.current = generation;
    const controller = new AbortController();
    pollingSession.current = { id: current.id, generation, controller };
    const isCurrent = () => !controller.signal.aborted
      && pollingGeneration.current === generation
      && pollingSession.current?.generation === generation
      && activeSessionId.current === current.id;
    setPollError("");
    try {
      const completed = await pollSession(current.id, value => { if (isCurrent()) update(value); }, 1000, controller.signal);
      if (!isCurrent()) return;
      if (completed.run_state === "COMPLETE") router.push("/results");
      if (completed.run_state === "FAILED") setPollError(completed.run_error ?? "검사를 완료하지 못했습니다. 다시 시도해 주세요.");
    } catch (pollingError) {
      if (!isCurrent()) return;
      setPollError(pollingError instanceof Error ? pollingError.message : "검사 진행 상태를 불러오지 못했습니다.");
    } finally {
      if (pollingSession.current?.generation === generation) pollingSession.current = null;
    }
  }
  useEffect(() => () => {
    pollingGeneration.current += 1;
    pollingSession.current?.controller.abort();
    pollingSession.current = null;
  }, [session?.id]);
  useEffect(() => {
    let active = true;
    if (!session?.files.length) {
      setReadiness(null);
      setAcknowledged(false);
      return;
    }
    request<SemanticReadiness>(`/sessions/${session.id}/semantic-readiness`)
      .then(value => { if (active) setReadiness(value); })
      .catch(value => { if (active) setPollError(value instanceof Error ? value.message : "내용 검토 준비 상태를 불러오지 못했습니다."); });
    return () => { active = false; };
  }, [session?.id, session?.files.length]);
  useEffect(() => {
    if (session?.run_state === "RUNNING") void resumePolling(session);
  }, [session?.id, session?.run_state]);
  async function choose(fixture: "demo-broken" | "demo-fixed") {
    if (!session) return;
    const manifest = await request<SubmissionFile[]>(`/demo-files/${fixture}`);
    const form = new FormData();
    for (const file of manifest) {
      const response = await fetch(`/api/demo-files/${fixture}/${encodeURIComponent(file.name)}`, { cache: "no-store" });
      if (!response.ok) throw new Error("demo 파일을 불러오지 못했습니다.");
      form.append("files", await response.blob(), file.name);
    }
    const next = await sessionRequest(session.id, "files", form);
    update(next);
    await loadReadiness(next);
    setSelected([]);
  }
  async function upload() {
    if (!session || !selected.length) return;
    const form = new FormData();
    selected.forEach(file => form.append("files", file));
    const next = await sessionRequest(session.id, "files", form);
    update(next);
    await loadReadiness(next);
    setSelected([]);
  }
  async function validate() {
    if (!session) return;
    try {
      const next = await sessionRequest(session.id, "validate", {
        semantic_text_ai_acknowledged: readiness?.ack_required ? acknowledged : false,
      });
      update(next);
      if (next.run_state === "RUNNING") {
        void resumePolling(next);
        return;
      }
      if (next.run_state === "COMPLETE") router.push("/results");
    } catch (error) {
      update(await request<CheckSession>(`/sessions/${session.id}`));
      throw error;
    }
  }
  function selectFiles(event: ChangeEvent<HTMLInputElement>) { setSelected(Array.from(event.target.files ?? [])); }
  return <WorkflowGuard step={recheck ? "recheck" : "upload"}><ModeNote /><PageTitle step={recheck ? "05 / RECHECK" : "03 / SUBMISSION UPLOAD"} title={recheck ? "수정한 파일로 다시 확인하세요" : "제출할 파일을 모아주세요"} description={recheck ? "수정 패키지를 선택하고 다시 검사하면 이전 판정과 달라진 항목을 보여줍니다." : "패키지에 포함된 파일을 확인한 뒤 제출 전 검사를 시작합니다."} />
    {session && <PreflightPackageWorkspace
      session={session} recheck={recheck} busy={busy} readiness={readiness} acknowledged={acknowledged}
      selected={selected} error={error} pollError={pollError} onSelectFiles={selectFiles}
      onUpload={() => void run(upload)} onChooseDemo={fixture => void run(() => choose(fixture))}
      onAcknowledge={setAcknowledged} onValidate={() => void run(validate)}
    />}
  </WorkflowGuard>;
}

const statuses: FindingStatus[] = ["BLOCKER", "REVIEW", "PASS", "EXTERNAL"];
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
function submissionEvidenceEmptyText(result: ValidationResult) {
  const semantic = result.semantic_review;
  if (semantic?.coverage === "FULL" && semantic.assessment === "NO_CLEAR_EVIDENCE") {
    return "제출파일에서 명확한 관련 근거 후보를 찾지 못했습니다. 직접 대조가 필요합니다.";
  }
  if (result.source_mode === "generic_review") {
    return "이 항목의 제출파일 검증은 실행되지 않았습니다. 직접 대조가 필요합니다.";
  }
  return undefined;
}
export function ResultsScreen() {
  const { session } = useSession();
  const [filter, setFilter] = useState<FindingStatus | "ALL">("ALL");
  const priority: Record<FindingStatus, number> = { BLOCKER: 0, REVIEW: 1, EXTERNAL: 2, PASS: 3 };
  const results = [...(session?.results ?? [])].sort((a, b) => priority[a.status] - priority[b.status]);
  const blockers = results.filter(result => result.status === "BLOCKER").length;
  const previous = session?.previous_results ?? [];
  const changes = results.flatMap(result => {
    const old = previous.find(item => item.requirement_id === result.requirement_id);
    return old && resultChanged(old, result) ? [{ old, result }] : [];
  });
  const statusChanges = changes.filter(({ old, result }) => old.status !== result.status);
  const title = blockers ? "제출 전, 수정이 필요합니다" : session?.status === "READY" ? "자동 확인 가능한 필수 조건을 충족했습니다." : previous.some(result => result.status === "BLOCKER") ? "수정 완료. 직접 확인할 항목이 남았어요" : "직접 확인할 항목이 남았어요";
  return <WorkflowGuard step="results"><ModeNote /><PageTitle step="04 / PREFLIGHT RESULTS" title="근거를 확인하고, 제출을 준비하세요" description="판정별 근거와 필요한 조치를 확인한 뒤 수정한 파일로 다시 검사할 수 있습니다." />
    <section className={`result-banner ${blockers ? "has-blocker" : ""}`} aria-label="전체 검사 상태"><div className="result-title"><span className="alert-symbol">{blockers ? "!" : "↗"}</span><div><span className="eyebrow">{session?.status} · CHECK {String(session?.revision ?? 1).padStart(2, "0")}</span><h2>{title}</h2><p>{blockers ? `BLOCKER ${blockers}개를 수정한 후 재검사하세요.` : "자동 확인 가능한 필수 조건의 결과와 남아 있는 REVIEW 항목을 함께 확인하세요."}</p></div></div><Link className="button primary" href="/recheck">수정 후 재검사 →</Link></section>
    {previous.length > 0 && <section className="comparison" aria-label="재검사 비교"><strong>이전 검사와 비교</strong><span>{statusChanges.length}개 판정 변경</span>{changes.map(({ old, result }) => old.status !== result.status ? <span className="change" key={result.id}>{result.requirement_id} <Badge status={old.status} /><span>→</span><Badge status={result.status} /></span> : <span className="change" key={result.id}>{result.requirement_id} 내용 근거 상태가 변경되었습니다.<br />이전: {semanticState(old)}<br />현재: {semanticState(result)}</span>)}{changes.length === 0 && <span>변경된 판정이 없습니다.</span>}</section>}
    <div className="results-heading"><div className="filter-tabs" aria-label="판정 필터"><button aria-pressed={filter === "ALL"} onClick={() => setFilter("ALL")}>전체 <b>{results.length}</b></button>{statuses.map(status => <button key={status} aria-pressed={filter === status} onClick={() => setFilter(status)}>{status} <b>{results.filter(r => r.status === status).length}</b></button>)}</div><span className="muted">{session?.validation_profile === "generic" ? "Generic Profile · 확인된 계획의 코드 검사" : "근거 기반 검사 결과 · v1.5"}</span></div>
    <section className="findings" aria-label="검사 결과 목록">{results.filter(r => filter === "ALL" || r.status === filter).map(result => <article className="finding" key={result.id} aria-label={`${result.requirement_id} ${result.title}`}><div className="finding-heading"><Badge status={result.status} /><span className="rule-id">{result.requirement_id}</span><h3>{result.title}</h3></div><p>{result.explanation}</p><div className="evidence-grid"><EvidenceBox label="공고문 근거" evidence={result.announcement_evidence} /><EvidenceBox label="제출파일 근거" evidence={result.submission_evidence} emptyText={submissionEvidenceEmptyText(result)} /></div>{result.semantic_review && result.semantic_review.evidence.length > 1 && <section className="semantic-evidence"><span className="evidence-label">추가 근거 후보</span>{result.semantic_review.evidence.slice(1, 3).map((evidence, index) => <EvidenceBox key={`${evidence.locator}-${index}`} label={`근거 후보 ${index + 2}`} evidence={evidence} />)}</section>}{result.semantic_review?.reason_code && <details><summary>기술 세부</summary><code>{result.semantic_review.reason_code}</code></details>}<div className="action-line"><span>다음 조치</span>{result.action}</div></article>)}
      {results.filter(r => filter === "ALL" || r.status === filter).length === 0 && <div className="empty-inline">이 상태의 판정은 없습니다.</div>}
    </section><div className="results-footer"><span>{session?.validation_profile === "generic" ? "사람이 확정한 요구사항과 게이트를 통과한 계획만 코드로 검사했습니다. REVIEW / EXTERNAL은 직접 확인하세요." : "원본 Validator v1.5의 실제 검사 결과입니다. REVIEW 항목과 최종 제출은 직접 확인하세요."}</span><Link href="/recheck" className="text-link">수정 패키지 재검사 →</Link></div>
  </WorkflowGuard>;
}
