# FINAL CHECK — AI Submission Preflight
Version: 1.0 | Product lock supplied by Product / Business Lead on 2026-09-02.

## Ownership and source of truth
ChatGPT planning: Product / Business Lead. Codex: AI / Engineering Lead.
This file is the implementation source of truth. The eventual confirmed GitHub repository is the shared source of truth for both leads. Local work is provisional until that repository is supplied.
Product decisions must be recorded in IMPLEMENTATION_ISSUES.md, never silently resolved in code.

## Product
“공고문과 실제 제출파일을 넣으면, AI가 제출 전에 탈락요인을 찾아주고 각 판정의 근거까지 보여준다.”

## Locked golden path
1. Home — start a check, choose the clearly labelled demo.
2. Announcement Analysis — inspect extracted requirements and announcement evidence.
3. Submission Upload — inspect selected submission files and run preflight.
4. Preflight Results — read findings, both evidence sources, and corrections.
5. Recheck — replace the submission package, run again, compare the previous result.

The routes are /, /announcement, /upload, /results, /recheck. Empty or expired sessions provide a recovery link. Recheck returns to Results without introducing a sixth screen.

## Locked finding statuses
BLOCKER, REVIEW, PASS, EXTERNAL.
BLOCKER always requires nonempty announcement evidence AND submission evidence.
Missing evidence cannot produce BLOCKER or an optimistic PASS.
SubmissionStatus is a separate conservative summary: NOT_CHECKED, BLOCKED, NEEDS_REVIEW, READY. READY requires a complete nonempty result set with only PASS. EXTERNAL remains unresolved and prevents READY in this skeleton; final external-attestation UX is an open product issue.

## R19 lock
- PHOTO_ONLY suspicion: REVIEW.
- Ken Burns / pan / zoom: REVIEW.
- Ambiguous motion: REVIEW.
- Confident real motion: no R19 issue.
- Never automatically emit R19 BLOCKER.

## Technical lock
Next.js + TypeScript frontend; FastAPI + Python backend.
Preserve the original Python Validator v1.5. Do not rewrite its algorithm in another language.
First validate the mock UI in a real browser, then implement the Python adapter boundary.
No login, payments, team collaboration, admin, analytics dashboard, automatic submission, vertical expansion, or incidental SaaS features.

## TASK 01 scope
Typed CheckSession, Requirement, ValidationResult and SubmissionStatus.
Accessible responsive five-screen UI, FastAPI skeleton, explicitly mocked requirement/result fixtures, broken/fixed recheck, real browser smoke, and truthful execution record.
Demo rules, evidence and files are synthetic examples only; they are not official announcement requirements or the previous 39-package benchmark.
Real arbitrary uploads can be selected and received, but extraction/validation stays unavailable until verified engines are supplied. Never attach demo PASS/BLOCKER findings to arbitrary user files.

## User-reported technical gate (not rerun in TASK 01)
Requirement Extractor independent blind test PASS; Validator v1.5 Final Full Gate PASS.
39 new synthetic PDF/MP4 packages after freeze.
Critical blocker, deterministic blocker, text-PDF semantic, scanned-PDF vision and evidence coverage: 100% as reported. Vision was a same-session visual test.
Dangerous submission to READY: 0%; normal submission to BLOCKED: 0%.
These are handoff claims, not independently verified artifacts in this checkout. Kill Test is closed; do not restart it.

## Demo acceptance
Broken package: two evidence-backed BLOCKER findings plus R19 REVIEW and EXTERNAL.
Fixed package: the deterministic blockers clear; R19 and EXTERNAL remain REVIEW/EXTERNAL. The UI must never imply that clearing blockers means full READY.
Every screen visibly states demo/mock mode. Uploaded custom package shows unavailable analysis explicitly.
