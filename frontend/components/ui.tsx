"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useSession } from "./session-provider";
import type { Evidence, FindingStatus, SubmissionFile } from "@/types/check";

export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true); setError("");
    try { await action(); }
    catch (err) { setError(err instanceof Error ? err.message : "작업을 완료하지 못했습니다."); }
    finally { setBusy(false); }
  }
  return { busy, error, run };
}
const steps = [
  ["/", "Home", "시작"], ["/announcement", "Announcement Analysis", "공고 분석"],
  ["/upload", "Submission Upload", "파일 업로드"], ["/results", "Preflight Results", "검사 결과"],
  ["/recheck", "Recheck", "재검사"],
];
export function Navigation() {
  const path = usePathname();
  const { session } = useSession();
  const current = steps.findIndex(([url]) => url === path);
  return <nav aria-label="검사 단계" className="step-nav">{steps.map(([url, english, name], i) => {
    const enabled = i === 0 || (i < 3 ? Boolean(session?.announcement_name) : i === 3 ? Boolean(session?.results.length) : (session?.revision ?? 0) > 0);
    const content = <><span className="step-num">{String(i + 1).padStart(2, "0")}</span><span><small>{english}</small>{name}</span></>;
    return enabled ? <Link href={url} key={url} className={i === current ? "step active" : "step"} aria-current={i === current ? "step" : undefined}>{content}</Link>
      : <span key={url} className="step disabled" aria-disabled="true">{content}</span>;
  })}</nav>;
}
export function Badge({ status }: { status: FindingStatus }) {
  return <span className={`badge ${status.toLowerCase()}`}>{status}</span>;
}
export function ModeNote() {
  const { session } = useSession();
  if (session?.generic_profile) {
    const verifierReady = session.source_mode === "generic_verifier";
    return <div className="mode-note"><span className="dot" />
      <strong>GENERIC · {session.generic_profile.execution_kind ?? "실행 전"}{verifierReady ? " · CODE CHECK" : ""}</strong>
      <span>{verifierReady
        ? "사람이 확정한 요구사항과 게이트를 통과한 계획만 코드로 검사합니다. 현재 지원 PDF / MP4. 스캔 PDF Vision 미연결."
        : "AI 요구사항 후보는 사람의 검토·확정이 필요합니다. 자동 검사 계획 전에는 REVIEW / EXTERNAL. 스캔 PDF Vision 미연결."}</span>
    </div>;
  }
  return <div className="mode-note"><span className="dot" /><strong>{session?.validation_profile ? "DEMO FILES · VALIDATOR v1.5" : "임의 공고 · 분석 미연결"}</strong>
    <span>{session?.validation_profile ? "실제 파일을 동결 규칙으로 검사합니다. 스캔 PDF Vision 미연결 → REVIEW." : "공고 추출기가 연결되지 않아 요구사항과 판정을 만들지 않습니다."}</span></div>;
}
export function Guard({ children, requireResults = false }: { children: ReactNode; requireResults?: boolean }) {
  const { session, loading, recoveryError } = useSession();
  if (loading) return <div className="empty" role="status">검사 세션을 불러오는 중입니다…</div>;
  if (!session?.announcement_name || (requireResults && !session.results.length)) return <div className="empty">
    <span className="eyebrow">START A CHECK</span><h1>먼저 검사를 시작해 주세요</h1>
    <p>{recoveryError || (requireResults ? "아직 완료된 검사 결과가 없습니다." : "공고를 선택하면 이 단계를 진행할 수 있습니다.")}</p>
    <Link className="button primary" href="/">홈으로 돌아가기 →</Link>
    {session?.announcement_name && <Link className="button secondary" href="/upload">제출파일 선택</Link>}
  </div>;
  return <>{children}</>;
}
export function PageTitle({ step, title, description }: { step: string; title: string; description: string }) {
  return <div className="page-heading"><div><span className="eyebrow">{step}</span><h1>{title}</h1><p>{description}</p></div><span className="stamp">FINAL<br />CHECK<span>SUBMISSION PREFLIGHT</span></span></div>;
}
export function EvidenceBox({ label, evidence, emptyText }: { label: string; evidence: Evidence | null; emptyText?: string }) {
  return <div className="evidence"><span className="evidence-label">{label}</span>
    {evidence ? <><blockquote>{evidence.excerpt}</blockquote><small>{evidence.source} · {evidence.locator}</small></>
      : <p className="muted">{emptyText ?? "제출파일로 확인할 수 없는 외부 항목입니다."}</p>}</div>;
}
export function FileList({ files }: { files: SubmissionFile[] }) {
  return <ul className="file-list">{files.map(file => <li key={file.name}><span className="file-icon">{file.name.toLowerCase().endsWith(".mp4") ? "MP4" : "PDF"}</span><div><strong>{file.name}</strong><small>{(file.size_bytes / 1024).toFixed(1)} KB · {file.media_type}</small></div><span className="file-check" aria-label="선택됨">✓</span></li>)}</ul>;
}
export function ErrorNotice({ error }: { error: string }) {
  return error ? <div className="error-note" role="alert" aria-label="작업 오류">{error}</div> : null;
}
