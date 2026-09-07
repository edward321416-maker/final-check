"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession, FindingStatus, SubmissionFile } from "@/types/check";
import { useSession } from "./session-provider";
import { Badge, ErrorNotice, EvidenceBox, FileList, Guard, ModeNote, PageTitle, useAction } from "./ui";
import { GenericProfileReview, TextAnnouncementInput } from "./generic-profile";

export function HomeScreen() {
  const router = useRouter();
  const { update } = useSession();
  const { busy, error, run } = useAction();
  const [announcement, setAnnouncement] = useState<File | null>(null);
  async function startDemo() {
    const session = await request<CheckSession>("/sessions", { mode: "demo" });
    update(await sessionRequest(session.id, "demo-announcement", {}));
    router.push("/announcement");
  }
  async function startCustom() {
    if (!announcement) return;
    const session = await request<CheckSession>("/sessions", { mode: "custom" });
    const form = new FormData(); form.append("file", announcement);
    update(await sessionRequest(session.id, "announcement", form));
    router.push("/announcement");
  }
  return <><section className="hero"><div className="hero-copy"><span className="eyebrow"><span className="dot" /> AI SUBMISSION PREFLIGHT</span>
    <h1>제출 버튼을 누르기 전,<br /><span>마지막 한 번의 확인.</span></h1>
    <p className="hero-description">공고문과 제출파일을 함께 확인하고,<br />탈락으로 이어질 수 있는 문제를 근거와 함께 살펴보세요.</p>
    <div className="hero-actions"><button className="button primary large" disabled={busy} onClick={() => void run(startDemo)}>{busy ? "검사 준비 중…" : "demo 검사 시작하기"}<span>↗</span></button><span className="muted">로그인 없이 · 5단계 체험</span></div>
    <p className="demo-caption">원본 Validator v1.5가 실제 예시 파일을 검사합니다. 내 공고는 실제 AI 후보를 사람이 확정한 뒤 안전한 일부 조건만 코드로 검사합니다. Vision은 미연결입니다.</p>
  </div><div className="preview" aria-label="demo 결과 미리보기"><div className="preview-top"><span>CHECK REPORT / SAMPLE</span><span className="tiny-tag">EXAMPLE</span></div>
    <div className="preview-score"><span className="alert-symbol">!</span><div><small>제출 전 수정이 필요합니다</small><strong>2개의 BLOCKER</strong></div></div>
    <div className="preview-finding"><Badge status="BLOCKER" /><strong>개인정보 동의서 누락</strong><p>공고에는 필수 첨부, 제출파일에는 없음.</p><div className="mini-evidence"><span>공고 근거 ✓</span><span>제출 근거 ✓</span></div></div>
    <div className="preview-finding subtle"><Badge status="REVIEW" /><strong>영상 내용 확인 필요</strong><p>사진 구성 의심은 사람이 확인합니다.</p></div>
    <div className="preview-bottom">문제 발견 <span>→</span> 근거 확인 <span>→</span> 수정 후 재검사</div>
  </div></section>
  <section className="home-bottom"><div><span className="eyebrow">01 / START WITH YOUR ANNOUNCEMENT</span><h2>내 공고문으로 시작하기</h2><p>텍스트를 붙여 넣거나 PDF / UTF-8 TXT를 선택하세요. 원문 근거를 확인한 뒤 요구사항을 직접 승인합니다. 파일은 10 MiB, PDF는 50페이지까지 지원합니다.</p>
    <p className="info-note">입력한 공고 내용은 이 PC의 ChatGPT 인증 Codex CLI를 통해 AI 요구사항 분석에 사용됩니다.</p>
    <TextAnnouncementInput />
    <div className="inline-upload"><label className="file-picker"><span>공고문 선택</span><input aria-label="공고문 파일" type="file" accept=".pdf,.txt" disabled={busy} onChange={e => setAnnouncement(e.target.files?.[0] ?? null)} /></label>
      {announcement && <span className="selected-name">{announcement.name}</span>}
      <button className="button secondary" disabled={!announcement || busy} onClick={() => void run(startCustom)}>파일 정보 확인 →</button></div><ErrorNotice error={error} />
  </div><aside className="principle"><span className="eyebrow">EVIDENCE FIRST</span><h3>판정만큼 중요한 건,<br />그 판정의 근거.</h3><p>모든 BLOCKER는 공고문과 제출파일,<br />두 곳의 근거를 함께 보여줍니다.</p></aside></section>
  <div className="status-legend"><span><Badge status="BLOCKER" /> 수정 필요</span><span><Badge status="REVIEW" /> 직접 검토</span><span><Badge status="PASS" /> 조건 충족</span><span><Badge status="EXTERNAL" /> 외부 확인</span></div></>;
}

export function AnnouncementScreen() {
  const { session } = useSession();
  return <Guard><ModeNote /><PageTitle step="01 / ANNOUNCEMENT ANALYSIS" title="공고의 조건부터 확인하세요" description="제출 전에 지켜야 할 조건과 공고문에 적힌 근거를 살펴봅니다." />
    {session?.generic_profile ? <GenericProfileReview /> : <>
    <div className="content-grid"><section className="panel"><div className="panel-heading"><h2>동결 공고 요구사항</h2><span>{session?.requirements.length ?? 0}개 항목</span></div>
      {session?.requirements.length ? session.requirements.map(rule => <details className="requirement" key={rule.id} open><summary><span className="rule-id">{rule.id}</span><strong>{rule.title}</strong><span className="verifier">{rule.verifier}</span></summary><p>{rule.description}</p><EvidenceBox label="공고문 근거" evidence={rule.announcement_evidence} /></details>)
        : <div className="empty-inline"><h3>실제 공고 분석은 아직 연결되지 않았습니다</h3><p>공고문 파일명만 수신했습니다. 요구사항을 임의로 만들지 않습니다.</p></div>}
    </section><aside className="side-panel"><span className="eyebrow">ANNOUNCEMENT</span><h3>{session?.announcement_name}</h3><p>{session?.mode === "demo" ? "동결 엔진에 포함된 숏폼 공고 발췌입니다. 원문 공고 PDF를 자동 추출한 결과는 아닙니다." : "파일을 읽어 판정하는 기능은 다음 단계에서 연결합니다."}</p><hr /><strong>다음은 제출파일입니다</strong><p>어떤 파일을 검사할지 확인한 뒤 preflight를 실행합니다.</p><Link href="/upload" className="button primary full">제출파일 선택하기 →</Link></aside></div>
    </>}
  </Guard>;
}

export function UploadScreen({ recheck = false }: { recheck?: boolean }) {
  const { session, update } = useSession();
  const router = useRouter();
  const { busy, error, run } = useAction();
  const [selected, setSelected] = useState<File[]>([]);
  async function choose(fixture: "demo-broken" | "demo-fixed") {
    if (!session) return;
    const manifest = await request<SubmissionFile[]>(`/demo-files/${fixture}`);
    const form = new FormData();
    for (const file of manifest) {
      const response = await fetch(`/api/demo-files/${fixture}/${encodeURIComponent(file.name)}`, { cache: "no-store" });
      if (!response.ok) throw new Error("demo 파일을 불러오지 못했습니다.");
      form.append("files", await response.blob(), file.name);
    }
    update(await sessionRequest(session.id, "files", form));
    setSelected([]);
  }
  async function upload() {
    if (!session || !selected.length) return;
    const form = new FormData();
    selected.forEach(file => form.append("files", file));
    update(await sessionRequest(session.id, "files", form));
    setSelected([]);
  }
  async function validate() {
    if (!session) return;
    try {
      update(await sessionRequest(session.id, "validate", {}));
    } catch (error) {
      update(await request<CheckSession>(`/sessions/${session.id}`));
      throw error;
    }
    router.push("/results");
  }
  function selectFiles(event: ChangeEvent<HTMLInputElement>) { setSelected(Array.from(event.target.files ?? [])); }
  const previous = session?.results.length ? session.results : session?.previous_results ?? [];
  return <Guard><ModeNote /><PageTitle step={recheck ? "04 / RECHECK" : "02 / SUBMISSION UPLOAD"} title={recheck ? "수정한 파일로 다시 확인하세요" : "제출할 파일을 모아주세요"} description={recheck ? "수정 패키지를 선택하고 다시 검사하면 이전 판정과 달라진 항목을 보여줍니다." : "패키지에 포함된 파일을 확인한 뒤 제출 전 검사를 시작합니다."} />
    <div className="content-grid"><section className="panel"><div className="panel-heading"><h2>{recheck ? "수정 패키지" : "제출 패키지"}</h2><span>{session?.files.length ?? 0}개 파일</span></div>
      {session?.mode === "demo" && <div className="fixture-options"><button className={`fixture-option ${session.fixture === "demo-broken" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-broken"} disabled={busy} onClick={() => void run(() => choose("demo-broken"))}><span className="fixture-kicker">DEMO / BEFORE</span><strong>문제 있는 demo 불러오기</strong><small>개인정보 동의서 누락 · 영상 61초</small></button><button className={`fixture-option ${session.fixture === "demo-fixed" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-fixed"} disabled={busy} onClick={() => void run(() => choose("demo-fixed"))}><span className="fixture-kicker">DEMO / AFTER</span><strong>수정한 demo 불러오기</strong><small>개인정보 동의서 복원 · 영상 45초</small></button></div>}
      {session?.files.length ? <FileList files={session.files} /> : <div className="empty-inline"><span className="upload-glyph">↑</span><h3>검사할 패키지를 선택해 주세요</h3><p>demo 패키지를 불러오거나 아래에서 내 파일을 선택하세요.</p></div>}
      <details className="custom-upload" open={session?.mode === "custom"}><summary>내 제출파일 선택하기</summary><p>현재 MVP 자동 검사 지원: PDF / MP4. 최대 8개 파일을 지원하며 배포 환경의 업로드 제한이 적용됩니다. 확인된 검사 계획만 코드로 실행하며 나머지는 직접 확인해야 합니다.</p><p className="info-note">제출 파일은 현재 자동 형식 검사를 위해 FINAL CHECK 서버에서 처리되며, TASK09의 AI Planner에는 전송되지 않습니다. 개인정보·회사 기밀이 없는 테스트 파일 사용을 권장합니다.</p><label className="file-picker"><span>파일 찾아보기</span><input aria-label="제출파일" type="file" multiple accept=".pdf,.mp4" disabled={busy} onChange={selectFiles} /></label>{selected.length > 0 && <div><p>{selected.map(file => file.name).join(", ")}</p><button className="button secondary" disabled={busy} onClick={() => void run(upload)}>선택한 {selected.length}개 파일 확인</button></div>}</details>
      <ErrorNotice error={error} />
    </section><aside className="side-panel"><span className="eyebrow">{recheck ? "RECHECK CHECKLIST" : "BEFORE YOU CHECK"}</span><h3>{recheck ? "무엇을 바꾸셨나요?" : "파일의 근거까지 함께"}</h3>
      {recheck && previous.length > 0 ? <ul className="checklist">{previous.filter(r => r.status === "BLOCKER").map(r => <li key={r.id}>{r.action}</li>)}</ul> : <p>필수 서류와 영상 조건을 확인하고, 문제가 있으면 수정 방법을 안내합니다.</p>}
      <div className="info-note">R19 사진 구성 의심은 자동 BLOCKER가 되지 않습니다. 사람의 검토가 필요합니다.</div>
      <button className="button primary full" disabled={busy || !session?.files.length || selected.length > 0} onClick={() => void run(validate)}>{busy ? "확인 중…" : recheck ? "재검사 실행하기 →" : "Preflight 실행하기 →"}</button>
      <Link href={recheck && session?.results.length ? "/results" : "/announcement"} className="text-link">{recheck && session?.results.length ? "이전 결과 보기" : "← 공고 조건 다시 보기"}</Link>
    </aside></div>
  </Guard>;
}

const statuses: FindingStatus[] = ["BLOCKER", "REVIEW", "PASS", "EXTERNAL"];
export function ResultsScreen() {
  const { session } = useSession();
  const [filter, setFilter] = useState<FindingStatus | "ALL">("ALL");
  const priority: Record<FindingStatus, number> = { BLOCKER: 0, REVIEW: 1, EXTERNAL: 2, PASS: 3 };
  const results = [...(session?.results ?? [])].sort((a, b) => priority[a.status] - priority[b.status]);
  const blockers = results.filter(result => result.status === "BLOCKER").length;
  const previous = session?.previous_results ?? [];
  const changes = results.filter(result => previous.some(old => old.requirement_id === result.requirement_id && old.status !== result.status));
  const title = blockers ? "제출 전, 수정이 필요합니다" : session?.status === "READY" ? "검사한 조건을 모두 충족했습니다" : previous.some(result => result.status === "BLOCKER") ? "수정 완료. 직접 확인할 항목이 남았어요" : "직접 확인할 항목이 남았어요";
  return <Guard requireResults><ModeNote /><PageTitle step="03 / PREFLIGHT RESULTS" title="근거를 확인하고, 제출을 준비하세요" description="판정별 근거와 필요한 조치를 확인한 뒤 수정한 파일로 다시 검사할 수 있습니다." />
    <section className={`result-banner ${blockers ? "has-blocker" : ""}`} aria-label="전체 검사 상태"><div className="result-title"><span className="alert-symbol">{blockers ? "!" : "↗"}</span><div><span className="eyebrow">{session?.status} · CHECK {String(session?.revision ?? 1).padStart(2, "0")}</span><h2>{title}</h2><p>{blockers ? `BLOCKER ${blockers}개를 수정한 후 재검사하세요.` : "REVIEW와 EXTERNAL을 직접 확인하기 전에는 제출 준비 완료로 판단하지 않습니다."}</p></div></div><Link className="button primary" href="/recheck">수정 후 재검사 →</Link></section>
    {previous.length > 0 && <section className="comparison" aria-label="재검사 비교"><strong>이전 검사와 비교</strong><span>{changes.length}개 판정 변경</span>{changes.map(result => <span className="change" key={result.id}>{result.requirement_id} <Badge status={previous.find(old => old.requirement_id === result.requirement_id)!.status} /><span>→</span><Badge status={result.status} /></span>)}{changes.length === 0 && <span>변경된 판정이 없습니다.</span>}</section>}
    <div className="results-heading"><div className="filter-tabs" aria-label="판정 필터"><button aria-pressed={filter === "ALL"} onClick={() => setFilter("ALL")}>전체 <b>{results.length}</b></button>{statuses.map(status => <button key={status} aria-pressed={filter === status} onClick={() => setFilter(status)}>{status} <b>{results.filter(r => r.status === status).length}</b></button>)}</div><span className="muted">{session?.validation_profile === "generic" ? "Generic Profile · 확인된 계획의 코드 검사" : "근거 기반 검사 결과 · v1.5"}</span></div>
    <section className="findings" aria-label="검사 결과 목록">{results.filter(r => filter === "ALL" || r.status === filter).map(result => <article className="finding" key={result.id} aria-label={`${result.requirement_id} ${result.title}`}><div className="finding-heading"><Badge status={result.status} /><span className="rule-id">{result.requirement_id}</span><h3>{result.title}</h3></div><p>{result.explanation}</p><div className="evidence-grid"><EvidenceBox label="공고문 근거" evidence={result.announcement_evidence} /><EvidenceBox label="제출파일 근거" evidence={result.submission_evidence} emptyText={result.source_mode === "generic_review" ? "이 항목의 제출파일 검증은 실행되지 않았습니다. 직접 대조가 필요합니다." : undefined} /></div><div className="action-line"><span>다음 조치</span>{result.action}</div></article>)}
      {results.filter(r => filter === "ALL" || r.status === filter).length === 0 && <div className="empty-inline">이 상태의 판정은 없습니다.</div>}
    </section><div className="results-footer"><span>{session?.validation_profile === "generic" ? "사람이 확정한 요구사항과 게이트를 통과한 계획만 코드로 검사했습니다. REVIEW / EXTERNAL은 직접 확인하세요." : "원본 Validator v1.5의 실제 검사 결과입니다. REVIEW 항목과 최종 제출은 직접 확인하세요."}</span><Link href="/recheck" className="text-link">수정 패키지 재검사 →</Link></div>
  </Guard>;
}
