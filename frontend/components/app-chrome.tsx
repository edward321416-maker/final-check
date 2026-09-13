"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useSession } from "@/components/session-provider";
import { WORKFLOW_STEPS, canEnterStep, isStepComplete } from "@/lib/workflow";

export function Brand() {
  return <Link href="/" className="brand" aria-label="FINAL CHECK 홈">
    <span className="scan-check" aria-hidden="true"><span>✓</span></span>
    <span>FINAL CHECK</span>
  </Link>;
}

export function AppChrome({ children }: { children: ReactNode }) {
  const path = usePathname();
  const { session } = useSession();
  const landing = path === "/";

  return <>
    <header className={`site-header ${landing ? "landing-header" : "app-header"}`}>
      <Brand />
      {landing && <>
        <nav className="product-nav" aria-label="제품 소개">
          <Link href="#how-it-works">How it works</Link>
          <Link href="#evidence-first">Evidence-first</Link>
          <Link href="#verification">검증 방식</Link>
        </nav>
        <Link className="button primary" href="#start-check">제출 전 검사 시작하기</Link>
      </>}
    </header>
    <div className={path === "/results" ? "shell shell-results" : "shell"}>
      {!landing && <nav aria-label="검사 단계" className="step-nav">
        {WORKFLOW_STEPS.map(step => {
          const active = path === step.href;
          const enabled = canEnterStep(session, step.key);
          const complete = isStepComplete(session, step.key);
          const content = <><span className="step-num">{complete ? "✓" : step.number}</span><span>{step.label}</span></>;
          return enabled
            ? <Link key={step.key} href={step.href} className={`step${active ? " active" : ""}`} aria-current={active ? "step" : undefined}>{content}</Link>
            : <span key={step.key} className="step disabled" aria-disabled="true">{content}</span>;
        })}
      </nav>}
      <main id="main">{children}</main>
      <footer className="site-footer"><strong>FINAL CHECK</strong><span>확신은, 근거에서 시작됩니다.</span></footer>
    </div>
  </>;
}
