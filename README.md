# FINAL CHECK — AI Submission Preflight
공고문과 실제 제출파일을 넣으면, AI가 제출 전에 탈락요인을 찾아주고 각 판정의 근거까지 보여준다.

TASK 03 adds a generic announcement → human-reviewed requirement profile → validation handoff path to the existing five-screen UI. Its default extractor is local rules, **not an external AI model**. Generic automatic submission verification is unsupported and returns REVIEW/EXTERNAL.
TASK 02 connects the original **frozen Validator v1.5** to real multipart uploads and remains unchanged in behavior.
The demo uses newly generated synthetic files. Its findings come from actual Python execution, not canned JSON.
[Product lock](docs/PRODUCT_SPEC_V1.md) · [Actual execution report](RESULT_CODEX.md) · [Demo script](docs/DEMO_SCRIPT.md)

TASK04 independently measured the unchanged local extractor on eight real
announcements with 173 pre-output frozen Gold requirements: recall 18.50%, precision
15.17%, modality accuracy 25.00%. Exact quotes were 100%, semantic support 24.17%.
This is a same-agent manual benchmark, not independent human adjudication.
[Report and limitations](benchmarks/task04/report/report.md). Engineering recommends
an AI-first comparison for Product Lead review; no AI provider or TASK05 work is added.

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
- Custom text/text-PDF announcements use a separate generic profile, explicit per-item approval and whole-profile confirmation. No custom announcement inherits frozen rules.
- R19 uncertainty → REVIEW. R20/R21 licensing and provenance → REVIEW. No unsupported automatic PASS/BLOCKER.
- Scanned PDF Vision is unavailable → REVIEW, incomplete. No invented model result.
- Submission status: BLOCKED / REVIEW_REQUIRED / READY. Before a run: null plus run_state=NOT_STARTED.
- Upload receipts, temporary files and raw outputs are isolated per local session; removed on replacement/expiry/shutdown. In-memory sessions expire after one hour or restart.
- No auth, payment, analytics, automatic submission, remote AI call or public app deployment.
- A public source repository is distinct from a publicly hosted application.
- The exact historical 39-case corpus was not included or rerun. Its report is reference evidence only.

## Generic announcement review
On Home, paste the source text or choose a UTF-8 TXT/text-based PDF. Run "요구사항 추출 실행" on Announcement Analysis.
Review each original quote and its source offset; edit/delete candidates, keep NEEDS_REVIEW or approve each item. Check the full-source acknowledgement and choose "Profile 확정" before handing off to validation.
PDF input limit: 10 MiB, 50 pages, 100,000 extracted characters; no OCR/Vision. Textless pages require Vision and cannot produce a confirmed profile.
The local provider uses narrow Korean patterns. Confidence 0.5 is uncalibrated. It can miss rules, misclassify modality/conditions or require manual splitting. No recall/precision or universal competition coverage is claimed.
The generic pipeline checks actual upload identity but does not test submission compliance. Its findings remain REVIEW/EXTERNAL and its summary REVIEW_REQUIRED.
Canonical schemas: backend/app/models/profiles.py and frontend/types/profile.ts. Provider interface: backend/app/services/extractors.py. Human review: backend/app/services/profiles.py. Generic handoff: backend/app/services/generic_validation.py.
New checks run with the same pytest and Playwright commands above. To regenerate only TASK 03 synthetic PDF fixtures: `backend/.venv/Scripts/python.exe -X utf8 scripts/generate_announcement_fixtures.py`. Fixture generation and expected candidates are from the same session, so comparisons are SELF-BENCHMARK, not independent accuracy evidence.

## Layout
frontend/: existing Next.js routes, UI and browser smoke.
backend/: FastAPI, typed schema, session storage, immutable frozen source and adapter.
fixtures/v15/: real broken/fixed submissions.
artifacts/: raw/adapted results, independent audit, tests and screenshots.
docs/: product policy, demo, original handoff/reference gate.
scripts/: fixture generation, audit, acceptance and local launcher.
