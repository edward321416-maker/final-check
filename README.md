# FINAL CHECK — AI Submission Preflight
공고문과 실제 제출파일을 넣으면, AI가 제출 전에 탈락요인을 찾아주고 각 판정의 근거까지 보여준다.

TASK 01 is a working **mock MVP skeleton**. Actual Requirement Extractor / Validator v1.5 integration is unavailable until original sources are supplied.
Product source of truth: [docs/PRODUCT_SPEC_V1.md](docs/PRODUCT_SPEC_V1.md).
Actual execution evidence: [RESULT_CODEX.md](RESULT_CODEX.md).

## Structure
- frontend/: Next.js App Router, TypeScript contracts and Playwright browser smoke.
- backend/: FastAPI, Pydantic, in-memory local session store and unavailable Python validator adapter.
- fixtures/: synthetic announcement, demo-broken / demo-fixed PDF/MP4 and mocked results.
- docs/: product lock, validator policy and click-through demo script.
- artifacts/: actual test reports, fixture verification and browser screenshots.
- scripts/: local launcher and fixture tooling.

## Setup (Windows PowerShell)
Prerequisites used here: Node 24, Python 3.14, FFmpeg (only to regenerate/verify demo media).
From the project root:
```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
powershell -File scripts/start-local.ps1
```
Open http://127.0.0.1:3100. API docs: http://127.0.0.1:8100/docs.
The launcher starts hidden local processes, saves their IDs/logs under ignored artifacts/runtime, and refuses occupied ports.
Stop only these launcher processes with `powershell -File scripts/stop-local.ps1`.

For development, use two terminals:
```powershell
# Terminal 1, backend directory
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100
# Terminal 2, frontend directory
npm run dev
```
On macOS/Linux use python3 and backend/.venv/bin/python instead. The Windows launcher itself is Windows-only.
API_ORIGIN can override the Next.js server-side proxy target; no browser-exposed credentials are used.

## Verification
Stop the demo launcher before smoke tests: Playwright deliberately requires free 3100/8100 ports.
```powershell
# From backend/
.venv/Scripts/python.exe -m pytest -q --junitxml=../artifacts/backend-smoke.xml
# From frontend/
npm run typecheck
npm run build
npx playwright install chromium
npm run test:smoke
```
Playwright starts/stops the production frontend and FastAPI for each suite; runs desktop Chromium and mobile Chromium emulation. No mocked network is used for the golden path. Only the explicit outage test intercepts one request.
Generated media are committed; regenerate with `python scripts/generate_fixtures.py`.
Verify with `python scripts/verify_fixtures.py`.

## Boundaries
No login, payment, analytics, automatic submission, team/admin features or remote AI call.
Data are per-session and in-memory, with a one-hour TTL and 100-session cap.
Actual upload content is discarded after metadata hashing. PDF/MP4 are accepted by extension in this skeleton; content safety/semantic validity is not asserted. Limits: 8 files, 20 MiB each, 40 MiB aggregate.
R19 can never automatically BLOCKER. Clearing blockers does not clear REVIEW/EXTERNAL.
The reported 39-package freeze benchmark was **NOT TESTED** here.
The intended GitHub repository is unconfirmed; this standalone local repository has no remote.
