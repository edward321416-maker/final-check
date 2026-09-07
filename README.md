# FINAL CHECK — AI Submission Preflight
공고문과 실제 제출파일을 넣으면, AI가 제출 전에 탈락요인을 찾아주고 각 판정의 근거까지 보여준다.

TASK 08 adds the first **typed generic verifier MVP**: AI proposes a closed plan from a human-confirmed profile, code gates it, and deterministic PDF/MP4 checkers measure actual submission bytes. AI never decides PASS/BLOCKER/READY/BLOCKED; ambiguity remains REVIEW.
All file checks that depend on a declared PDF/MP4 type use actual type confirmation before a definite result: PDF signature plus parser, or a successful ffprobe MP4 container result. Inspection failure and extension/content mismatch remain REVIEW outside FILE_TYPE; FILE_TYPE MP4 reports VIOLATION only after a successful definite non-MP4 probe.
TASK 07 keeps the TASK06 **actual local two-stage AI provider** and adds a restart-safe single-node runtime: SQLite session/job metadata, durable local artifacts, checkpoint resume, bounded explicit retry, and mandatory human confirmation.
TASK 02 connects the original **frozen Validator v1.5** to real multipart uploads and remains unchanged in behavior.
The demo uses newly generated synthetic files. Its findings come from actual Python execution, not canned JSON.
[Product lock](docs/PRODUCT_SPEC_V1.md) · [Actual execution report](RESULT_CODEX.md) · [TASK08 typed verifier](docs/TASK08_TYPED_VERIFIER.md) · [TASK07 durable runtime](docs/TASK07_DURABLE_RUNTIME.md) · [TASK06 extraction](docs/TASK06_TWO_STAGE_MVP.md) · [Demo script](docs/DEMO_SCRIPT.md)

TASK04 independently measured the unchanged local extractor on eight real
announcements with 173 pre-output frozen Gold requirements: recall 18.50%, precision
15.17%, modality accuracy 25.00%. Exact quotes were 100%, semantic support 24.17%.
This is a same-agent manual benchmark, not independent human adjudication.
[Report and limitations](benchmarks/task04/report/report.md). TASK05 preserved a separate
blind AI comparison; TASK06 integrates the locked two-stage product architecture without rescoring it.

Replay the saved benchmark and verify frozen hashes with
`backend/.venv/Scripts/python.exe -X utf8 scripts/run_task04_benchmark.py`.
Existing output is reused; source collection and Gold rewriting refuse after freeze.

## Local setup
Verified runtime: Node 24, Python 3.14, FFmpeg/ffprobe 8.1.2.
PowerShell from the project root:
```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
powershell -File scripts/start-local.ps1
```
Open http://127.0.0.1:3100; API docs http://127.0.0.1:8100/docs.
Stop the recorded local processes with `powershell -File scripts/stop-local.ps1`.
The launcher starts hidden loopback processes and refuses occupied ports.
On macOS/Linux, use python3 and backend/.venv/bin/python; start uvicorn and Next manually.

Development terminals:
```powershell
# backend/
.venv/Scripts/python.exe -X utf8 -m uvicorn app.main:app --host 127.0.0.1 --port 8100
# frontend/
npm run dev
```

## Verification
Stop the launcher before Playwright; it starts its own production frontend and API.
From the project root:
```powershell
backend/.venv/Scripts/python.exe -X utf8 scripts/audit_v15_fixtures.py
backend/.venv/Scripts/python.exe -X utf8 scripts/run_v15_acceptance.py
```
From backend/: `.venv/Scripts/python.exe -X utf8 -m pytest -q --junitxml=../artifacts/backend-smoke.xml`.
From frontend/: `npm run typecheck`, `npm run build`, `npx playwright install chromium`, `npm run test:smoke`.
Normal golden-path requests use actual files and the actual engine without API interception. The isolated outage scenario intentionally returns an injected error.

New fixtures are committed under fixtures/v15/. Regenerate using the backend Python runtime and scripts/generate_v15_fixtures.py; always audit before scoring.
Historical TASK 01 fixtures stay in their original directories and are never used for v1.5 acceptance.

## Contract and limits
- Frozen source hash: 4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11.
- Native engine input: a directory of files. App adaptation is in backend/app/validators/v15_adapter.py.
- Supported announcement profile: the provided childcare short-form competition SOURCE_RULES, with fixed 테스트어린이집 file names.
- Custom text/text-PDF announcements use a separate generic profile, explicit per-item approval and whole-profile confirmation. No custom announcement inherits frozen rules. After confirmation, the typed verifier can automate only source-grounded closed PDF/MP4 checks.
- R19 uncertainty → REVIEW. R20/R21 licensing and provenance → REVIEW. No unsupported automatic PASS/BLOCKER.
- Scanned PDF Vision is unavailable → REVIEW, incomplete. No invented model result.
- Submission status: BLOCKED / REVIEW_REQUIRED / READY. Before a run: null plus run_state=NOT_STARTED.
- Session/profile/job metadata and announcement/submission/raw artifacts persist under `FINAL_CHECK_DATA_DIR` (default `.final-check/runtime/`). Safe expired sessions are removed after one hour; active/retryable jobs are protected. Backend restart no longer invalidates a session.
- This is a single-node, single-backend-process durability contract. Multi-worker coordination is unsupported.
- No product login, payment, analytics, automatic submission or public app deployment. The default generic extractor and planner use the already authenticated local Codex CLI; no production AI service is selected.
- A public source repository is distinct from a publicly hosted application.
- The exact historical 39-case corpus was not included or rerun. Its report is reference evidence only.

## Generic announcement review
On Home, paste the source text or choose a UTF-8 TXT/text-based PDF. Run "요구사항 추출 실행" on Announcement Analysis. The actual local provider may take longer than 30 seconds; the UI starts a background extraction and polls its status.
Review each original quote and its source offset; edit/delete candidates, keep NEEDS_REVIEW or approve each item. Check the full-source acknowledgement and choose "Profile 확정" before handing off to validation.
PDF input limit: 10 MiB, 50 pages, 100,000 extracted characters; no OCR/Vision. Textless pages require Vision and cannot produce a confirmed profile.
Stage 1/2 outputs remain provisional and may miss, duplicate or misclassify requirements. More than 100 candidates is explicit overflow and runs in batches of 50; 500 is the hard ceiling. Local rules are an explicitly selected fallback suggestion path, never a silent provider-failure substitute. No new recall/precision or universal competition coverage is claimed.
After profile confirmation, choose "자동 검사 계획 생성". The isolated planner sees the confirmed source/profile only; it never sees submission data. The deterministic gate authorizes only closed, source-grounded plans. `generic_review` remains REVIEW/EXTERNAL only, while `generic_verifier` may issue evidence-backed PASS/BLOCKER from actual bytes. Conditional, ambiguous, unsupported, failed or untrusted-type checks remain REVIEW. Current MVP automatic file support: PDF / MP4.
Canonical schemas: backend/app/models/profiles.py, backend/app/models/verifier_plans.py, frontend/types/profile.ts and frontend/types/check.ts. Durable job/storage contracts: backend/app/models/jobs.py, backend/app/services/jobs.py and backend/app/services/storage.py. Provider boundaries: backend/app/services/ai_providers.py and backend/app/services/verifier_planner.py. Human review and deterministic gates: backend/app/services/profiles.py and backend/app/services/verifier_compiler.py. Generic checking/policy: backend/app/services/generic_inspection.py, backend/app/services/verifier_engine.py and backend/app/services/generic_policy.py.
New checks run with the same pytest and Playwright commands above. To regenerate only TASK 03 synthetic PDF fixtures: `backend/.venv/Scripts/python.exe -X utf8 scripts/generate_announcement_fixtures.py`. Fixture generation and expected candidates are from the same session, so comparisons are SELF-BENCHMARK, not independent accuracy evidence.

## TASK09 zero-cost public deployment

The competition MVP keeps the existing ChatGPT-authenticated Codex CLI (`FINAL_CHECK_AI_PROVIDER=codex`) for Stage1, Stage2, and Planner. Human confirmation and the deterministic Plan Gate retain verdict authority. Railway Hobby, OpenAI API billing, and the OpenAI Responses production provider are deferred.

The local Next.js production server is exposed only through the account-assigned ngrok Free HTTPS development domain. FastAPI, SQLite/session files, Codex authentication, and ffprobe stay on the host PC. Deployment settings and operator steps are in [TASK09 public deployment](docs/TASK09_PUBLIC_DEPLOYMENT.md), [operator runbook](docs/TASK09_OPERATOR_RUNBOOK.md), and [judging runbook](docs/JUDGING_RUNBOOK.md).

Judge availability depends on the host PC/network. There is no cloud failover, ngrok Free outbound transfer is limited to 1 GB/month, and no production SLA is claimed.

## Layout
frontend/: existing Next.js routes, UI and browser smoke.
backend/: FastAPI, typed schema, SQLite/local-artifact runtime, immutable frozen source and adapter.
fixtures/v15/: real broken/fixed submissions.
artifacts/: raw/adapted results, independent audit, tests and screenshots.
docs/: product policy, demo, original handoff/reference gate.
scripts/: fixture generation, audit, acceptance and local launcher.
