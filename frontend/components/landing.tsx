"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { request, sessionRequest } from "@/lib/api";
import type { CheckSession } from "@/types/check";
import { TextAnnouncementInput } from "./generic-profile";
import { useSession } from "./session-provider";
import { Badge, ErrorNotice, useAction } from "./ui";

export function LandingScreen() {
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
    const form = new FormData();
    form.append("file", announcement);
    update(await sessionRequest(session.id, "announcement", form));
    router.push("/announcement");
  }

  return <>
    <section className="hero landing-hero">
      <div className="hero-copy">
        <span className="eyebrow">AI SUBMISSION PREFLIGHT</span>
        <h1>제출 버튼을 누르기 전, 마지막 확인.</h1>
        <p className="hero-description">FINAL CHECK가 공고의 요구사항을 구조화하고, 실제 제출파일에서 놓친 조건과 근거를 찾아줍니다.</p>
        <div className="hero-actions">
          <a className="button primary large" href="#start-check">제출 전 검사 시작하기</a>
          <a className="button secondary" href="#how-it-works">어떻게 작동하나요?</a>
        </div>
        <p className="trust-line">AI는 근거를 찾고, 확실한 조건은 코드가 검증합니다.</p>
      </div>
      <section className="product-frame mini-product" aria-label="Preflight 결과 예시">
        <div className="mini-window-heading"><span>CHECK REPORT</span><small>EXAMPLE</small></div>
        <div className="mini-summary"><span>1 BLOCKER</span><span>1 REVIEW</span><span>3 PASS</span></div>
        <div className="mini-labels" aria-hidden="true"><span>RULE</span><span>EVIDENCE</span><span>VERDICT</span></div>
        <div className="mini-chain"><strong>영상 60초 이내</strong><span>61.0s</span><b className="status-text blocker">BLOCKER</b></div>
        <div className="mini-chain"><strong>기대효과 포함</strong><span>proposal.pdf · p.2</span><b className="status-text review">REVIEW</b></div>
        <small className="example-note">EXAMPLE · 실제 판정 구조를 축약한 예시</small>
      </section>
    </section>

    <section className="landing-story" id="how-it-works" aria-labelledby="story-title">
      <div className="story-intro">
        <span className="eyebrow">HOW IT WORKS</span>
        <h2 id="story-title">공고에서 근거 있는 Preflight까지</h2>
        <p>사람이 확정한 요구사항을 기준으로, 실제 제출파일에서 확인한 근거를 연결합니다.</p>
      </div>

      <article className="story-step">
        <div className="story-copy"><span className="story-number">01</span><h3>공고 읽기</h3><p>공고 원문에서 요구사항 후보와 정확한 출처를 함께 구조화합니다. 후보는 아직 공식 규칙이 아닙니다.</p></div>
        <div className="product-frame story-frame" aria-label="공고 읽기 예시">
          <div className="source-sample"><span>공고 원문 · p.1</span><mark>영상은 60초 이내로 제출</mark></div>
          <div className="story-arrow" aria-hidden="true">→</div>
          <div className="candidate-sample"><small>요구사항 후보</small><strong>영상 60초 이내</strong><span>AI EXTRACTED · 사람 확인 필요</span></div>
        </div>
      </article>

      <article className="story-step reverse" id="evidence-first">
        <div className="product-frame story-frame review-frame" aria-label="기준 확정 예시">
          <span className="frame-kicker">SOURCE EVIDENCE</span>
          <blockquote>“영상은 60초 이내로 제출”</blockquote>
          <div className="confirmation-line"><span>AI EXTRACTED</span><span aria-hidden="true">→</span><strong>HUMAN CONFIRMED</strong></div>
        </div>
        <div className="story-copy"><span className="story-number">02</span><h3>기준 확정</h3><p>원문과 후보를 사람이 직접 비교하고 승인합니다. 이 확인이 제출 검사의 기준을 확정합니다.</p></div>
      </article>

      <article className="story-step emphasis" id="verification">
        <div className="story-copy"><span className="story-number">03</span><h3>제출물 검증</h3><p>자동 판정 가능한 항목은 공고 근거와 실제 측정/제출 근거를 연결하고, 의미 판단은 REVIEW로 남깁니다.</p></div>
        <div className="product-frame story-frame evidence-frame" aria-label="제출물 검증 예시">
          <div><small>RULE</small><strong>영상 60초 이내</strong></div>
          <span className="evidence-link" aria-hidden="true">→</span>
          <div><small>EVIDENCE</small><strong>submission.mp4 · 61.0s</strong></div>
          <span className="evidence-link" aria-hidden="true">→</span>
          <div><small>VERDICT</small><b className="status-text blocker">BLOCKER</b></div>
        </div>
      </article>
    </section>

    <section className="home-bottom" id="start-check">
      <div>
        <span className="eyebrow">START WITH YOUR ANNOUNCEMENT</span>
        <h2>내 공고문으로 시작하기</h2>
        <p>텍스트를 붙여 넣거나 PDF / UTF-8 TXT를 선택하세요. 원문 근거를 확인한 뒤 요구사항을 직접 승인합니다. 파일은 10 MiB, PDF는 50페이지까지 지원합니다.</p>
        <TextAnnouncementInput />
        <div className="inline-upload">
          <label className="file-picker"><span>공고문 선택</span><input aria-label="공고문 파일" type="file" accept=".pdf,.txt" disabled={busy} onChange={event => setAnnouncement(event.target.files?.[0] ?? null)} /></label>
          {announcement && <span className="selected-name">{announcement.name}</span>}
          <button className="button secondary" disabled={!announcement || busy} onClick={() => void run(startCustom)}>파일 정보 확인 →</button>
        </div>
        <ErrorNotice error={error} />
      </div>
      <aside className="start-demo">
        <span className="eyebrow">REAL DEMO</span>
        <h3>실제 예시 파일로 먼저 확인하세요</h3>
        <p>원본 Validator v1.5가 예시 PDF와 MP4를 같은 제출 경로에서 검사합니다. Vision은 연결되지 않았습니다.</p>
        <button className="button primary full" disabled={busy} onClick={() => void run(startDemo)}>{busy ? "검사 준비 중…" : "demo 검사 시작하기 →"}</button>
      </aside>
    </section>

    <div className="status-legend"><span><Badge status="BLOCKER" /> 수정 필요</span><span><Badge status="REVIEW" /> 직접 검토</span><span><Badge status="PASS" /> 조건 충족</span><span><Badge status="EXTERNAL" /> 외부 확인</span></div>
  </>;
}
