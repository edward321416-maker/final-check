"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession, FindingStatus } from "@/types/check";
import { useSession } from "./session-provider";
import { Badge, ErrorNotice, EvidenceBox, FileList, Guard, ModeNote, PageTitle, useAction } from "./ui";

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
    <p className="demo-caption">현재는 mock 기반 MVP입니다. 실제 AI 분석 결과가 아닙니다.</p>
  </div><div className="preview" aria-label="demo 결과 미리보기"><div className="preview-top"><span>CHECK REPORT / SAMPLE</span><span className="tiny-tag">MOCK</span></div>
    <div className="preview-score"><span className="alert-symbol">!</span><div><small>제출 전 수정이 필요합니다</small><strong>2개의 BLOCKER</strong></div></div>
    <div className="preview-finding"><Badge status="BLOCKER" /><strong>참가 동의서 누락</strong><p>공고에는 필수 첨부, 제출파일에는 없음.</p><div className="mini-evidence"><span>공고 근거 ✓</span><span>제출 근거 ✓</span></div></div>
    <div className="preview-finding subtle"><Badge status="REVIEW" /><strong>영상 내용 확인 필요</strong><p>사진 구성 의심은 사람이 확인합니다.</p></div>
    <div className="preview-bottom">문제 발견 <span>→</span> 근거 확인 <span>→</span> 수정 후 재검사</div>
  </div></section>
  <section className="home-bottom"><div><span className="eyebrow">01 / START WITH YOUR ANNOUNCEMENT</span><h2>내 공고문으로 시작하기</h2><p>PDF 또는 TXT 파일을 선택하세요. 현재 실제 파일은 수신만 하며, 분석 엔진은 연결 준비 중입니다.</p>
    <div className="inline-upload"><label className="file-picker"><span>공고문 선택</span><input aria-label="공고문 파일" type="file" accept=".pdf,.txt" disabled={busy} onChange={e => setAnnouncement(e.target.files?.[0] ?? null)} /></label>
      {announcement && <span className="selected-name">{announcement.name}</span>}
      <button className="button secondary" disabled={!announcement || busy} onClick={() => void run(startCustom)}>파일 정보 확인 →</button></div><ErrorNotice error={error} />
  </div><aside className="principle"><span className="eyebrow">EVIDENCE FIRST</span><h3>판정만큼 중요한 건,<br />그 판정의 근거.</h3><p>모든 BLOCKER는 공고문과 제출파일,<br />두 곳의 근거를 함께 보여줍니다.</p></aside></section>
  <div className="status-legend"><span><Badge status="BLOCKER" /> 수정 필요</span><span><Badge status="REVIEW" /> 직접 검토</span><span><Badge status="PASS" /> 조건 충족</span><span><Badge status="EXTERNAL" /> 외부 확인</span></div></>;
}

export function AnnouncementScreen() {
  const { session } = useSession();
  return <Guard><ModeNote /><PageTitle step="01 / ANNOUNCEMENT ANALYSIS" title="공고의 조건부터 확인하세요" description="제출 전에 지켜야 할 조건과 공고문에 적힌 근거를 살펴봅니다." />
    <div className="content-grid"><section className="panel"><div className="panel-heading"><h2>추출된 요구사항</h2><span>{session?.requirements.length ?? 0}개 항목</span></div>
      {session?.requirements.length ? session.requirements.map(rule => <details className="requirement" key={rule.id} open><summary><span className="rule-id">{rule.id}</span><strong>{rule.title}</strong><span className="verifier">{rule.verifier}</span></summary><p>{rule.description}</p><EvidenceBox label="공고문 근거" evidence={rule.announcement_evidence} /></details>)
        : <div className="empty-inline"><h3>실제 공고 분석은 아직 연결되지 않았습니다</h3><p>공고문 파일명만 수신했습니다. 요구사항을 임의로 만들지 않습니다.</p></div>}
    </section><aside className="side-panel"><span className="eyebrow">ANNOUNCEMENT</span><h3>{session?.announcement_name}</h3><p>{session?.mode === "demo" ? "화면 체험을 위한 가상 공고입니다. 실제 공모전의 조건과 무관합니다." : "파일을 읽어 판정하는 기능은 다음 단계에서 연결합니다."}</p><hr /><strong>다음은 제출파일입니다</strong><p>어떤 파일을 검사할지 확인한 뒤 preflight를 실행합니다.</p><Link href="/upload" className="button primary full">제출파일 선택하기 →</Link></aside></div>
  </Guard>;
}

export function UploadScreen({ recheck = false }: { recheck?: boolean }) {
  const { session, update } = useSession();
  const router = useRouter();
  const { busy, error, run } = useAction();
  const [selected, setSelected] = useState<File[]>([]);
  async function choose(fixture: "demo-broken" | "demo-fixed") {
    if (!session) return;
    update(await sessionRequest(session.id, "fixture", { fixture }));
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
    update(await sessionRequest(session.id, "validate", {}));
    router.push("/results");
  }
  function selectFiles(event: ChangeEvent<HTMLInputElement>) { setSelected(Array.from(event.target.files ?? [])); }
  const previous = session?.results.length ? session.results : session?.previous_results ?? [];
  return <Guard><ModeNote /><PageTitle step={recheck ? "04 / RECHECK" : "02 / SUBMISSION UPLOAD"} title={recheck ? "수정한 파일로 다시 확인하세요" : "제출할 파일을 모아주세요"} description={recheck ? "수정 패키지를 선택하고 다시 검사하면 이전 판정과 달라진 항목을 보여줍니다." : "패키지에 포함된 파일을 확인한 뒤 제출 전 검사를 시작합니다."} />
    <div className="content-grid"><section className="panel"><div className="panel-heading"><h2>{recheck ? "수정 패키지" : "제출 패키지"}</h2><span>{session?.files.length ?? 0}개 파일</span></div>
      {session?.mode === "demo" && <div className="fixture-options"><button className={`fixture-option ${session.fixture === "demo-broken" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-broken"} disabled={busy} onClick={() => void run(() => choose("demo-broken"))}><span className="fixture-kicker">DEMO / BEFORE</span><strong>문제 있는 demo 불러오기</strong><small>동의서 누락 · 영상 12초</small></button><button className={`fixture-option ${session.fixture === "demo-fixed" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-fixed"} disabled={busy} onClick={() => void run(() => choose("demo-fixed"))}><span className="fixture-kicker">DEMO / AFTER</span><strong>수정한 demo 불러오기</strong><small>동의서 추가 · 영상 8초</small></button></div>}
      {session?.files.length ? <FileList files={session.files} /> : <div className="empty-inline"><span className="upload-glyph">↑</span><h3>검사할 패키지를 선택해 주세요</h3><p>demo 패키지를 불러오거나 아래에서 내 파일을 선택하세요.</p></div>}
      <details className="custom-upload" open={session?.mode === "custom"}><summary>내 제출파일 선택하기</summary><p>PDF · MP4 / 파일당 20 MiB, 최대 8개·합계 40 MiB. 실제 파일을 선택하면 demo 판정 대신 분석 미연결 상태로 전환됩니다.</p><label className="file-picker"><span>파일 찾아보기</span><input aria-label="제출파일" type="file" multiple accept=".pdf,.mp4" disabled={busy} onChange={selectFiles} /></label>{selected.length > 0 && <div><p>{selected.map(file => file.name).join(", ")}</p><button className="button secondary" disabled={busy} onClick={() => void run(upload)}>선택한 {selected.length}개 파일 확인</button></div>}</details>
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
  const results = session?.results ?? [];
  const blockers = results.filter(result => result.status === "BLOCKER").length;
  const previous = session?.previous_results ?? [];
  const changes = results.filter(result => previous.some(old => old.requirement_id === result.requirement_id && old.status !== result.status));
  const title = blockers ? "제출 전, 수정이 필요합니다" : session?.status === "READY" ? "검사한 조건을 모두 충족했습니다" : previous.some(result => result.status === "BLOCKER") ? "수정 완료. 직접 확인할 항목이 남았어요" : "직접 확인할 항목이 남았어요";
  return <Guard requireResults><ModeNote /><PageTitle step="03 / PREFLIGHT RESULTS" title="근거를 확인하고, 제출을 준비하세요" description="판정별 근거와 필요한 조치를 확인한 뒤 수정한 파일로 다시 검사할 수 있습니다." />
    <section className={`result-banner ${blockers ? "has-blocker" : ""}`} aria-label="전체 검사 상태"><div className="result-title"><span className="alert-symbol">{blockers ? "!" : "↗"}</span><div><span className="eyebrow">{session?.status} · CHECK {String(session?.revision ?? 1).padStart(2, "0")}</span><h2>{title}</h2><p>{blockers ? `BLOCKER ${blockers}개를 수정한 후 재검사하세요.` : "REVIEW와 EXTERNAL을 직접 확인하기 전에는 제출 준비 완료로 판단하지 않습니다."}</p></div></div><Link className="button primary" href="/recheck">수정 후 재검사 →</Link></section>
    {previous.length > 0 && <section className="comparison" aria-label="재검사 비교"><strong>이전 검사와 비교</strong><span>{changes.length}개 판정 변경</span>{changes.map(result => <span className="change" key={result.id}>{result.requirement_id} <Badge status={previous.find(old => old.requirement_id === result.requirement_id)!.status} /><span>→</span><Badge status={result.status} /></span>)}{changes.length === 0 && <span>변경된 판정이 없습니다.</span>}</section>}
    <div className="results-heading"><div className="filter-tabs" aria-label="판정 필터"><button aria-pressed={filter === "ALL"} onClick={() => setFilter("ALL")}>전체 <b>{results.length}</b></button>{statuses.map(status => <button key={status} aria-pressed={filter === status} onClick={() => setFilter(status)}>{status} <b>{results.filter(r => r.status === status).length}</b></button>)}</div><span className="muted">근거 기반 검사 결과 · MOCK</span></div>
    <section className="findings" aria-label="검사 결과 목록">{results.filter(r => filter === "ALL" || r.status === filter).map(result => <article className="finding" key={result.id} aria-label={`${result.requirement_id} ${result.title}`}><div className="finding-heading"><Badge status={result.status} /><span className="rule-id">{result.requirement_id}</span><h3>{result.title}</h3></div><p>{result.explanation}</p><div className="evidence-grid"><EvidenceBox label="공고문 근거" evidence={result.announcement_evidence} /><EvidenceBox label="제출파일 근거" evidence={result.submission_evidence} /></div><div className="action-line"><span>다음 조치</span>{result.action}</div></article>)}
      {results.filter(r => filter === "ALL" || r.status === filter).length === 0 && <div className="empty-inline">이 상태의 판정은 없습니다.</div>}
    </section><div className="results-footer"><span>이 결과는 mock demo입니다. 실제 제출 가능 여부를 보증하지 않습니다.</span><Link href="/recheck" className="text-link">수정 패키지 재검사 →</Link></div>
  </Guard>;
}
