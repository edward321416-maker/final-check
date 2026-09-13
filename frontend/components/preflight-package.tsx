"use client";

import Link from "next/link";
import type { ChangeEvent } from "react";
import type { CheckSession, CheckerType, SemanticReadiness } from "@/types/check";
import { ErrorNotice, FileList } from "./ui";

interface PreflightPackageWorkspaceProps {
  session: CheckSession;
  recheck: boolean;
  busy: boolean;
  readiness: SemanticReadiness | null;
  acknowledged: boolean;
  selected: File[];
  error: string;
  pollError: string;
  onSelectFiles: (event: ChangeEvent<HTMLInputElement>) => void;
  onUpload: () => void;
  onChooseDemo: (caseName: "demo-broken" | "demo-fixed") => void;
  onAcknowledge: (value: boolean) => void;
  onValidate: () => void;
}

export const CHECKER_LABEL: Record<CheckerType, string> = {
  FILE_PRESENCE: "파일 존재 여부",
  FILE_COUNT: "파일 개수",
  FILE_NAME: "파일명",
  FILE_TYPE: "파일 형식",
  FILE_SIZE: "파일 크기",
  PDF_PAGE_COUNT: "PDF 페이지 수",
  VIDEO_METADATA: "영상 길이/메타데이터",
};

function browserFileSize(file: File) {
  return `${(file.size / 1024).toFixed(1)} KB · ${file.type || "MIME 미확인"}`;
}

export function PreflightPackageWorkspace({
  session,
  recheck,
  busy,
  readiness,
  acknowledged,
  selected,
  error,
  pollError,
  onSelectFiles,
  onUpload,
  onChooseDemo,
  onAcknowledge,
  onValidate,
}: PreflightPackageWorkspaceProps) {
  const running = session.run_state === "RUNNING";
  const failed = session.run_state === "FAILED";
  const verifiedPlans = session.verification_plan?.plans.filter(plan => plan.status === "VERIFIED") ?? [];
  const checkerTypes = [...new Set(verifiedPlans.map(plan => plan.checker_type))];
  const manualPlanCount = session.verification_plan?.plans.filter(plan => plan.status !== "VERIFIED").length ?? 0;
  const semanticCount = readiness?.eligible_requirement_count ?? 0;
  const previous = session.results.length ? session.results : session.previous_results;
  const failure = error || session.run_error || pollError;
  const mutationLocked = busy || running;
  const validationDisabled = busy
    || !session.files.length
    || selected.length > 0
    || (Boolean(session.files.length) && readiness === null)
    || (readiness?.ack_required && !acknowledged)
    || running;

  return <div className="preflight-workspace">
    <section className="panel package-panel" aria-label={recheck ? "수정 패키지" : "제출 패키지"}>
      <div className="panel-heading">
        <div><span className="eyebrow">SUBMISSION PACKAGE</span><h2>{recheck ? "수정 패키지" : "제출 패키지"}</h2></div>
        <span>{session.files.length}개 파일</span>
      </div>

      {session.mode === "demo" && <div className="fixture-options">
        <button className={`fixture-option ${session.fixture === "demo-broken" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-broken"} disabled={mutationLocked} onClick={() => onChooseDemo("demo-broken")}>
          <span className="fixture-kicker">DEMO / BEFORE</span><strong>문제 있는 demo 불러오기</strong><small>수정 전 제출 패키지 예시</small>
        </button>
        <button className={`fixture-option ${session.fixture === "demo-fixed" ? "selected" : ""}`} aria-pressed={session.fixture === "demo-fixed"} disabled={mutationLocked} onClick={() => onChooseDemo("demo-fixed")}>
          <span className="fixture-kicker">DEMO / AFTER</span><strong>수정한 demo 불러오기</strong><small>수정 내용을 반영한 패키지 예시</small>
        </button>
      </div>}

      {session.files.length
        ? <FileList files={session.files} />
        : <div className="empty-inline"><span className="upload-glyph" aria-hidden="true">↑</span><h3>검사할 패키지를 선택해 주세요</h3><p>demo 패키지를 불러오거나 아래에서 내 파일을 선택하세요.</p></div>}

      <details className="custom-upload" open={session.mode === "custom"}>
        <summary>내 제출파일 선택하기</summary>
        <p>현재 MVP 자동 검사 지원: PDF / MP4. 최대 8개 파일을 지원하며 배포 환경의 업로드 제한이 적용됩니다. 확인된 검사 계획만 코드로 실행하며 나머지는 직접 확인해야 합니다.</p>
        <p className="info-note">제출 파일은 현재 자동 형식 검사를 위해 FINAL CHECK 서버에서 처리되며, TASK09의 AI Planner에는 전송되지 않습니다. 개인정보·회사 기밀이 없는 테스트 파일 사용을 권장합니다.</p>
        <label className="file-picker"><span>파일 찾아보기</span><input aria-label="제출파일" type="file" multiple accept=".pdf,.mp4" disabled={mutationLocked} onChange={onSelectFiles} /></label>
        {selected.length > 0 && <div className="selected-files" aria-label="선택한 파일">
          <ul>{selected.map(file => <li key={`${file.name}:${file.size}`}><span><strong>{file.name}</strong><small>{browserFileSize(file)}</small></span><em>선택됨</em></li>)}</ul>
          <button className="button secondary" disabled={mutationLocked} onClick={onUpload}>선택한 {selected.length}개 파일 확인</button>
        </div>}
      </details>

      <ErrorNotice error={failure} recovery={failed ? "현재 제출 패키지를 확인한 뒤 다시 실행할 수 있습니다." : undefined} />
    </section>

    <aside className="scope-panel" role="region" aria-label="이번 검사">
      <span className="eyebrow">{recheck ? "RECHECK SCOPE" : "WHAT WILL BE CHECKED"}</span>
      <h2>이번 검사</h2>
      {session.validation_profile === "frozen_v15" && <div className="scope-summary">
        <strong>{session.requirements.length}개 동결 Validator 항목</strong>
        <p>Validator v1.5에 저장된 제출 조건을 실제 파일에서 확인합니다.</p>
      </div>}
      {session.validation_profile === "generic" && <div className="scope-summary">
        <strong>{verifiedPlans.length}개 자동 검사 · {semanticCount}개 AI 근거 검토</strong>
        <p>사람이 확정한 요구사항 중 현재 계획과 내용 검토 준비 상태에 포함된 범위입니다.</p>
      </div>}

      <ul className="scope-list">
        {checkerTypes.map(checker => <li key={checker}><span aria-hidden="true">✓</span><div><strong>{CHECKER_LABEL[checker]}</strong><small>확인된 계획으로 코드 검사</small></div></li>)}
        {semanticCount > 0 && <li><span aria-hidden="true">◇</span><div><strong>PDF 내용 근거</strong><small>{semanticCount}개 요구사항 · 결과는 REVIEW</small></div></li>}
        {session.validation_profile === "frozen_v15" && <li><span aria-hidden="true">✓</span><div><strong>동결 제출 조건</strong><small>현재 세션의 Validator v1.5 범위</small></div></li>}
      </ul>

      {session.verification_plan_state === "REVIEW_REQUIRED" && <div className="scope-review-note">
        <strong>자동 검사 계획이 확정되지 않았습니다.</strong>
        <p>계획으로 컴파일되지 않은 결정적 항목은 REVIEW/수동 검토 범위로 남습니다.</p>
      </div>}
      {manualPlanCount > 0 && session.verification_plan_state !== "REVIEW_REQUIRED" && <p className="scope-footnote">{manualPlanCount}개 계획 항목은 REVIEW/수동 검토 범위입니다.</p>}

      {recheck && previous.length > 0 && <div className="recheck-summary"><h3>이전 BLOCKER 확인</h3><ul className="checklist">{previous.filter(result => result.status === "BLOCKER").map(result => <li key={result.id}>{result.action}</li>)}</ul></div>}

      <div className="authority-note"><strong>판정 권한</strong><p>코드로 확정할 수 없는 의미 판단과 R19 사진 구성 의심은 REVIEW로 남습니다.</p></div>

      {readiness?.ack_required && <div className="semantic-acknowledgement">
        <strong>AI 내용 검토 안내</strong>
        <p>원본 PDF 파일 자체는 AI에 전달되지 않습니다.<br />PDF에서 로컬로 추출한 전체 텍스트가 내용 요구사항 검토를 위해<br />ChatGPT 인증 Codex CLI를 통한 AI 분석에 사용됩니다.<br />MP4 내용은 AI로 분석하지 않습니다.</p>
        <label><input type="checkbox" checked={acknowledged} disabled={running} onChange={event => onAcknowledge(event.target.checked)} /> PDF에서 추출된 전체 텍스트가 AI 내용 검토에 사용되는 것을 확인했습니다.</label>
      </div>}

      {running && <p className="run-activity" role="status">{semanticCount > 0
        ? "객관적 조건과 PDF 내용 근거를 확인하고 있습니다."
        : "객관적 제출 조건을 확인하고 있습니다."}</p>}
      <button className="button primary full" disabled={validationDisabled} onClick={onValidate}>{busy ? "확인 중…" : recheck ? "재검사 실행하기" : "Preflight 실행하기"}</button>
      <Link href={recheck && session.results.length ? "/results" : session.mode === "custom" ? "/requirements" : "/announcement"} className="text-link">{recheck && session.results.length ? "이전 결과 보기" : session.mode === "custom" ? "← 요구사항 다시 보기" : "← 공고 조건 다시 보기"}</Link>
    </aside>
  </div>;
}
