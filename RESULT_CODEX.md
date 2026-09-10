# RESULT_CODEX — TASK 08

Date: 2026-09-07 (Asia/Seoul)

1. **TASK08 implementation:** MODIFY — 두 merge-blocking safety issue를 corrective change로 수정했으며 Product Lead 재검수를 기다린다.
2. **Baseline main SHA:** `fa3108db4074499ddefffca53e34f51bd7f95395` (TASK07 PR #9 merge commit).
3. **Issue:** [#10](https://github.com/edward321416-maker/final-check/issues/10), OPEN.
4. **Branch:** `issue/10-typed-verifier-compiler`.
5. **FINAL CHECK:** GO.
6. **Typed Verifier Compiler:** GO.
7. **Planner provider:** OpenAI through the existing ChatGPT-authenticated Codex CLI. No API key, paid API, new account or OAuth was added.
8. **Planner model:** `gpt-5.6-sol`, reasoning `high`.
9. **Planner prompt version:** `task08-planner-v1`.
10. **Planner prompt SHA-256:** `096fd93cd2c3770cd49dcdbe6131e0abda4ea8b3e074728dc7b45e219f36a4a6`. It was frozen before the first actual planner output and remained unchanged.
11. **Typed schema:** closed Pydantic/JSON schema `task08-verification-plan-v1`; extra keys, executable code, regex, paths, network instructions and arbitrary commands are rejected.
12. **Checker families:** `FILE_PRESENCE`, `FILE_COUNT`, `FILE_NAME`, `FILE_TYPE`, `FILE_SIZE`, `PDF_PAGE_COUNT`, `VIDEO_METADATA`.
13. **Plan gate:** REQUIRED and passing. Only code can assign `VERIFIED`; rejected or unsupported plans become `REVIEW_ONLY` or `EXTERNAL`.
14. **Parameter provenance:** exact evidence quote and offsets, source substring, normalized value and operator are persisted and deterministically grounded.
15. **Condition policy:** `condition != always` cannot enter the automatic verdict lane and becomes `REVIEW_ONLY`.
16. **Target ambiguity policy:** unresolved or non-unique targets return REVIEW; the checker never chooses a file semantically.
17. **False PASS policy:** STRICT. PASS requires a human-confirmed authoritative rule, valid PlanSet, VERIFIED plan, definite checker completion, unambiguous target, trusted actual PDF/MP4 type and actual submission evidence. Extension-only spoofing cannot PASS or READY.
18. **False BLOCKER policy:** automatic BLOCKER additionally requires mandatory modality, `severity=BLOCKER`, deterministic verifier, `condition=always` and a definite measured violation. ffprobe unavailable/timeout/malformed/execution failure remains REVIEW and cannot become BLOCKER.
19. **`generic_review` safety:** unchanged; it still permits REVIEW/EXTERNAL only.
20. **`generic_verifier` behavior:** PASS/BLOCKER is allowed only for a VERIFIED executable plan and always carries announcement evidence, submission evidence, plan ID, checker type, measured fact and expected constraint.
21. **PlanSet durability:** plan data and profile/source/confirmed-requirement bindings round-trip through the TASK07 SQLite session store. Abandoned planner RUNNING state becomes `REVIEW_REQUIRED` after restart.
22. **No-replan behavior:** the same valid PlanSet is reused after submission replacement; profile identity/version, confirmed requirement content, announcement SHA or text SHA changes invalidate it.
23. **Actual public announcement:** C01 public announcement exact excerpt `- 전체 길이 60초 이내 영상(최소 길이 제한 없음)`. The passing product run used actual TASK06 Stage1/Stage2, operator confirmation, the actual TASK08 planner, deterministic gate and actual upload/checker paths. Full C01/C02 source attempts were not claimed as passing E2E: earlier Stage1 malformed-output attempts and one transient provider-unavailable attempt were observed; the final exact-excerpt run passed on attempt 1.
24. **Broken submission ACTUAL result:** actual 61-second MP4 bytes measured by ffprobe as `duration_seconds=61.0`; plan `LTE 60 SECONDS`; finding BLOCKER; summary BLOCKED; both evidence sources present.
25. **Fixed submission ACTUAL result:** the same PlanSet checked actual 45-second MP4 bytes as `duration_seconds=45.0`; finding PASS; summary READY; both evidence sources present.
26. **Backend regression:** 144 passed. TASK08 has 67 focused contract/checker tests. The corrective TDD run reproduced the review findings as 7 failures before the common type-trust boundary was implemented.
27. **Browser regression:** fresh standard desktop/mobile suite 16 passed and 4 actual-AI opt-in cases skipped. TASK08 actual public-excerpt product E2E passed fresh once on the corrective code; the pre-existing TASK06 actual local-AI regression passed on the initial TASK08 head.
28. **Type/build/diff:** TypeScript typecheck PASS; production build PASS; `git diff --check` PASS.
29. **Gold lock:** 173 requirements; manifest SHA-256 `035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89`; unchanged and not scored.
30. **Frozen Validator lock:** SHA-256 `4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11`; unchanged. Generic inspection does not import the frozen metadata helper.
31. **Evidence classes:** ACTUAL — public excerpt, real local Codex Stage1/Stage2/planner calls, FastAPI/frontend, real MP4 bytes and ffprobe, durable PlanSet reuse; SELF — authored deterministic fixtures and unit/integration/browser tests; SIMULATED — malformed planner/schema/provider/parser/ffprobe/restart faults; NOT TESTED — public deployment, production provider availability, multiple workers/nodes, actual encrypted PDF, Vision/OCR, semantic submission verification, URL verification and formats other than PDF/MP4.
32. **Known limitations:** the planner remains a local authenticated CLI dependency; only closed file and metadata constraints are automated; unsupported wording, qualifiers and target semantics deliberately require review. The passing public E2E is an exact C01 excerpt, not full-announcement coverage or an accuracy benchmark. GitHub's CodeRabbit status says success because automated review was skipped and manual review is required; it is not treated as a substantive review pass.
33. **Next recommendation:** Product Lead reviews the open PR and actual evidence, then chooses the next scope. No deployment, semantic, Vision/OCR or format-expansion task is preselected.
34. **Commit history:** original TASK08 commit `d64c5d53871a5f53f49d381344260d61a25a1e80` is preserved; the new corrective head SHA is supplied by the final delivery report.
35. **PR:** [#11](https://github.com/edward321416-maker/final-check/pull/11), OPEN / NOT MERGED / **DO NOT MERGE YET** until Product Lead re-review of the corrective head.

Direction locks: FINAL CHECK = GO; Typed Verifier Compiler = GO; TASK08 implementation = MODIFY; AI Planner = GO for the local MVP; AI verdict authority = NOT_ALLOWED; Plan Gate = REQUIRED; conditional automatic verification = NOT_ALLOWED; False PASS policy = STRICT; Generic deterministic verifier = GO; current file support = PDF / MP4; PR #11 = DO NOT MERGE YET.

Evidence is stored under `artifacts/task08/`, including the actual planner result, actual product E2E envelope, screenshots and backend JUnit output.

## TASK10 Task 6 resume fix round 1

Date: 2026-09-09 (Asia/Seoul)

- Scope: Important finding 1 only. Trusted reviewer provenance is captured before an attempted semantic review and retained in degraded result metadata and bounded raw output after timeout or schema rejection. Semantic output remains REVIEW-only; deterministic findings and provider/model configuration are unchanged.
- RED (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_api.py::test_attempted_semantic_failure_preserves_trusted_provider_and_prompt_provenance -q` -> expected `2 failed, 1 warning`; both cases observed missing `semantic_review.provider`.
- GREEN (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_api.py::test_attempted_semantic_failure_preserves_trusted_provider_and_prompt_provenance -q` -> `2 passed, 1 warning`.
- Relevant backend suite (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_api.py tests/test_task08_verifier.py tests/test_smoke.py -q` -> `119 passed, 1 warning`.
- Diff check: `git diff --check` -> PASS before commit.
- Modified files: `backend/app/services/task10_validation.py`, `backend/tests/test_task10_api.py`, `RESULT_CODEX.md`.
- Evidence label: SELF. Timeout and invalid-schema provider behavior used the existing simulated external-reviewer test double; no actual Codex provider call was made.
- NOT TESTED: actual Codex CLI timeout/schema failure, frontend/browser behavior, the full backend suite, deployment, multi-worker behavior, and production provider availability.

## TASK10 Task 7 resume fix round 1

Date: 2026-09-09 (Asia/Seoul)

- Scope: Important finding 2 and the related semantic-evidence minor finding only. Polling retries a transient GET failure with capped backoff while the server session remains RUNNING; a completed FULL `NO_CLEAR_EVIDENCE` semantic review now states that no clear candidate was found instead of claiming validation was not executed. API timeout, semantic authority, navigation, providers and product settings are unchanged.
- RED (frontend cwd): `npm run test:smoke -- task10-semantic-ui.spec.ts` -> expected `4 failed, 20 passed`; the new desktop/mobile transient-poll cases remained on `/upload`, and the new completed no-evidence copy cases could not find the truthful wording.
- Build preparation (frontend cwd): `npm run build` -> PASS. The Playwright configuration uses `next start`, so rebuilding was required for the browser suite to exercise changed source.
- Focused GREEN (frontend cwd): `npm run test:smoke -- task10-semantic-ui.spec.ts --grep "retries a transient|labels a completed"` -> `4 passed` across desktop/mobile.
- Task10 semantic UI (frontend cwd): `npm run test:smoke -- task10-semantic-ui.spec.ts` -> `24 passed` across desktop/mobile.
- Typecheck (frontend cwd): `npm run typecheck` -> PASS.
- Build (frontend cwd): `npm run build` -> PASS.
- Diff check: `git diff --check` -> PASS before commit.
- Modified files: `frontend/lib/poll-session.ts`, `frontend/components/screens.tsx`, `frontend/tests/task10-semantic-ui.spec.ts`, `RESULT_CODEX.md`.
- Evidence label: SELF. Playwright used mocked local HTTP responses, including a simulated transient 503; no public/ACTUAL AI test or provider call was run.
- NOT TESTED: actual network interruption/retry behavior against a live server, actual semantic provider execution, the complete frontend suite, deployment, multi-worker behavior, and production provider availability.

## TASK10 Task 8 — controlled fixtures and ACTUAL semantic E2E harness

Date: 2026-09-09 (Asia/Seoul)

- Added deterministic CJK PyMuPDF fixtures for an explicit Korean content requirement: text-native positive, missing-effect, prompt-injection, and raster-only scanned PDFs plus their announcement source.
- TDD RED (backend cwd): `./.venv/Scripts/python.exe -m pytest tests/test_task10_semantic_submission.py -q` -> `2 failed, 10 passed` before the generator/fixtures existed. GREEN -> `12 passed` after generator and fixed SHA/text-layer/exact-quote contracts were implemented.
- Final focused non-AI (backend cwd): `./.venv/Scripts/python.exe -m pytest tests/test_task10_semantic_submission.py tests/test_task10_semantic_provider.py tests/test_task10_semantic_evidence.py -q` -> `36 passed`. Frontend `npm run typecheck` -> PASS. Opt-in browser harness without its flag -> `1 skipped`. `git diff --check` -> PASS.
- The opt-in desktop ACTUAL test uses `TASK10_ACTUAL_AI=1` and the configured ChatGPT-authenticated Codex CLI; it requires acknowledgement, checks only REVIEW/generic_review, and writes a bounded artifact only after terminal positive and missing runs. It never persists full extracted document text or a full prompt payload.
- ACTUAL classification: **NOT TESTED for TASK10 Semantic terminal behavior**. An isolated local attempt did observe actual Stage1/Stage2 provenance (`OpenAI via ChatGPT-authenticated Codex CLI`, configured `gpt-5.6-sol`/`high`), then found and repaired an upload/readiness race in the new test. A fresh retry was interrupted before semantic terminal output. No success artifact or screenshots were retained; no evidence gate was weakened.
- Requested implementer model/effort: `gpt-5.6-terra`/`medium`; configured spawn override: UNKNOWN; agent-observed runtime metadata: UNKNOWN; token usage UNKNOWN.
- NOT TESTED: ACTUAL semantic positive/missing/recheck outcome, full backend/frontend suites, build, TASK08/TASK09 regressions, public runtime/deployment, multi-worker behavior, and production availability.

## TASK10 Task 8 fix round 1 — ACTUAL semantic acceptance

Date: 2026-09-09 (Asia/Seoul)

- The opt-in harness now asserts task10 semantic provider provenance separately from Stage1/Stage2: `OpenAI via ChatGPT-authenticated Codex CLI`, `execution_kind=ACTUAL`, and `task10-semantic-review-v1` prompt provenance.
- The human-confirmed rule is intentionally narrowed to expected-effect content. Positive evidence accepts any non-empty locally accepted excerpt only if it is an exact substring of the controlled expected-effect page; no arbitrary full model sentence is required.
- The flow is positive -> missing -> positive recheck. All terminal results are REVIEW: positive/recheck `RELATED_EVIDENCE_FOUND`; missing `FULL`/`NO_CLEAR_EVIDENCE`; evidence fingerprints differ; the REVIEW-to-REVIEW Korean comparison is asserted. Semantic never produces PASS/BLOCKER.
- Screenshots and bounded ACTUAL JSON are published only after every assertion passes. Artifact fields exclude the full extracted text and prompt payload.
- ACTUAL (fresh local isolated data, configured authenticated Codex provider): `npm run test:smoke -- task10-actual-semantic.spec.ts --project=desktop --reporter=list` -> `1 passed (55.5s)`. Positive accepted page-2 excerpt: `기대효과: 참여자의 접근성을 높이고 지역 협력의 지속성을 강화합니다.` Missing result: REVIEW/NO_CLEAR_EVIDENCE/FULL. Recheck: REVIEW/RELATED_EVIDENCE_FOUND with changed fingerprint.
- Focused backend (backend cwd): `./.venv/Scripts/python.exe -m pytest tests/test_task10_semantic_submission.py tests/test_task10_semantic_provider.py tests/test_task10_semantic_evidence.py -q` -> `36 passed`. Frontend typecheck and production build -> PASS. `git diff --check` -> PASS.
- Requested/configured implementer model/effort: `gpt-5.6-terra`/`medium`; observed agent runtime metadata UNKNOWN. Actual provider configuration was `gpt-5.6-sol`/`high`; token usage UNKNOWN.
- NOT TESTED: full backend/frontend suites, TASK08/TASK09 regression, public runtime/deployment, multi-worker behavior, and broad provider reliability.

## TASK10 Task 9 — adversarial safety acceptance

Date: 2026-09-10 (Asia/Seoul)

- Scope: adversarial acceptance only. Added no production interface or production-code change; provider/model/product configuration and evidence gates are unchanged.
- TDD RED (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_semantic_evidence.py tests/test_task10_api.py -q -k task9_adversarial` -> no Task 9 adversarial cases collected (`38 deselected`, exit `5`), demonstrating the requested acceptance coverage was absent.
- Focused GREEN (backend cwd): the same command after adding the adversarial cases -> `13 passed, 36 deselected, 1 warning`.
- Task 9 safety suite (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_semantic_evidence.py tests/test_task10_api.py tests/test_task10_runtime.py -q` -> `50 passed, 1 warning`.
- SELF: exact fabricated-quote rejection, closed verdict-field schema rejection, real partial-text PDF suppression, and API result assertions passed. Fabricated provider evidence never entered `submission_evidence` or serialized trusted API data; partial coverage never became a whole-document absence claim.
- SIMULATED: timeout, authentication unavailable, transport unavailable, invalid JSON, schema rejection, PublicGuard quota, and PublicGuard concurrency cases each preserved deterministic `G001 / PASS` and degraded only semantic `G002` to `REVIEW`.
- ACTUAL: existing ChatGPT-authenticated Codex configuration (`gpt-5.6-sol`, reasoning `high`) processed the controlled prompt-injection PDF. The terminal semantic outcome was `REVIEW / RELATED_EVIDENCE_FOUND`, overall `REVIEW_REQUIRED`, with no semantic `PASS` or `BLOCKER`. The opt-in desktop command passed `1` test in `1.1m`.
- Frontend verification: `npm run typecheck` -> PASS; `npm run build` -> PASS.
- Modified files: `backend/tests/test_task10_semantic_evidence.py`, `backend/tests/test_task10_api.py`, `frontend/tests/task10-actual-semantic.spec.ts`, `artifacts/task10/actual-semantic-e2e.json`, `artifacts/task10/adversarial-safety-acceptance.md`, and `RESULT_CODEX.md`.
- Requested implementer model/effort: `gpt-5.6-sol` / `high`. Configured spawn override: UNKNOWN. Agent-observed runtime metadata: UNKNOWN. Actual provider configuration observed in bounded evidence: `gpt-5.6-sol` / `high`. Token usage: UNKNOWN.
- NOT TESTED: public deployment, production provider reliability, multi-worker behavior, API-key/OAuth providers, Vision/OCR, or broad semantic accuracy. No push, PR, merge, paid credit, account rotation, or public service change was performed.
- Concern: the supplied repo-root pytest command requires `backend` on `PYTHONPATH`; the equivalent backend-working-directory command above is the passing execution. The existing Starlette/httpx deprecation warning remains unrelated.

## TASK10 Task 10 — final local regression and acceptance evidence

Date: 2026-09-10 (Asia/Seoul)

- Status: implementation complete at tested implementation HEAD `a87c2eb9637154b278c15fdaa2586693fbd14c86`; local verification complete; public ACTUAL NOT TESTED; **DO NOT MERGE pending Product Lead review**.
- Runtime metadata: requested override `gpt-5.6-sol` / `high`; configured override `gpt-5.6-sol` / `high` from controller spawn-tool evidence; actual/agent-observed runtime UNKNOWN; token usage UNKNOWN. The configured override is not proof of the actual runtime. ACTUAL provider configuration was the existing ChatGPT-authenticated Codex CLI with `gpt-5.6-sol` / `high`.
- Full backend (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests -q` -> `242 passed, 1 warning in 43.08s`.
- Focused TASK10 (backend cwd): `.\.venv\Scripts\python.exe -m pytest tests/test_task10_semantic_models.py tests/test_task10_semantic_submission.py tests/test_task10_semantic_provider.py tests/test_task10_semantic_evidence.py tests/test_task10_runtime.py tests/test_task10_api.py -q` -> `85 passed, 1 warning in 13.02s`.
- Fix 1 artifact-schema RED: deterministic `node -e` required-key check -> expected exit 1; 14 session/ledger/coverage/terminal-status keys were absent before the harness change. The same bounded check after both fresh ACTUAL runs -> `GREEN_REQUIRED_EVIDENCE_PRESENT`, exit 0.
- Frontend (frontend cwd): `npm run test:smoke -- --reporter=list` -> `40 passed, 10 skipped in 35.1s`; `npm run typecheck` -> PASS; `npm run build` -> PASS.
- TASK08 ACTUAL fix 1 guarded run (frontend cwd): `npm run test:smoke -- task08-actual-ai.spec.ts --project=desktop --reporter=list` with the documented opt-in/provider and isolated data -> `1 passed (46.7s)`. Session `5fa74d37-8fe0-43ab-bcc6-8dbeebd800a3`; PlanSet `ec4f71bd-db18-4671-8ee8-04536120a978`; 61s `BLOCKER/BLOCKED`; 45s `PASS/READY`. The harness queried SQLite by that session ID and asserted `EXTRACT=1`, `PLAN=1`, `SEMANTIC=0`, and deterministic `semantic_review=null` before writing the bounded artifact.
- TASK10 ACTUAL fix 1 guarded run (frontend cwd): `npm run test:smoke -- task10-actual-semantic.spec.ts --project=desktop --reporter=list` with the documented opt-in/provider and isolated data -> `1 passed (1.1m)`. Session `7dfacb8f-b146-4e4b-a6e5-425aa939eba7`; positive/missing/recheck/prompt-injection each `COMPLETE / REVIEW_REQUIRED` with item `REVIEW`; missing coverage `FULL`; no semantic PASS/BLOCKER. The harness asserted exact-session `EXTRACT=1`, `PLAN=0`, `SEMANTIC=4` before writing the bounded artifact.
- TASK10 prompt: `task10-semantic-review-v1`, SHA-256 `c242a7cdcc9d4a1feddba58ce9a02a8db488227fe8bf8cf8f050d152f0d469cf`. Frozen Validator, Gold, TASK06 Stage1/Stage2, TASK08 Planner, TASK10 design and TASK10 plan committed/working bytes all matched their locked hashes.
- Public status: the one authorized read-only GET to `https://uncoy-joelle-macrodont.ngrok-free.dev/api/health` returned HTTP 404 at `2026-09-09T15:24:39Z`; TASK09 public ACTUAL and TASK10 public ACTUAL were not rerun and remain NOT TESTED. No public service/deployment change occurred.
- Evidence classes: ACTUAL — local authenticated Codex TASK08/TASK10 flows and actual PDF/MP4 paths; SELF — full/focused backend and browser/static/build checks plus adversarial deterministic cases; SIMULATED — Task 9 failure matrix; NOT TESTED — public current-HEAD behavior, production reliability, multi-worker/node, OAuth/API-key providers, paid services, OCR/Vision, MP4 semantic, URL verification, and broad semantic accuracy.
- Fix round 1 changes are limited to `frontend/tests/task08-actual-ai.spec.ts`, `frontend/tests/task10-actual-semantic.spec.ts`, the bounded `artifacts/task08/actual-product-e2e.json` and `artifacts/task10/actual-semantic-e2e.json`, and evidence documentation. No production source changed.
- CI URLs: none because no push or PR was authorized. No push, PR, merge, deployment, paid credit, API key, account, product AI setting, or global configuration change was performed.
- Hygiene scope: `git diff --check a87c2eb9637154b278c15fdaa2586693fbd14c86..9a3ee1a5831b7be8255b78b88233a1f387f8cb24` -> PASS for the original Task10 docs commit. Fix 1 worktree `git diff --check 9a3ee1a5831b7be8255b78b88233a1f387f8cb24` -> PASS before commit; the exact committed fix range is a post-commit gate. Full branch `git diff --check d90f53ae8e20b8a51b3a4559a3e7e5651dd204a0..HEAD` is not PASS: expected exit 2 is limited to intentional Markdown two-space hard breaks in the immutable authority Spec/Plan. Their Git-blob SHA-256 values remain `8a3b29da055a184779ed99aae9ffba99857e71ad030473172aec1b387d4f5019` and `714bee99708b9cebe61d2eddae111c3faa8bcdd94e343a5e5020127cac3663de`; they were not normalized.

## TASK10 final-review fix round 1 — cancel stale semantic polling

Date: 2026-09-10 (Asia/Seoul)

- Start state: clean branch `task10-content-requirement-review` at `60148fe8ae13bb4720f458a25d463f50516505d2`, with approved baseline `d90f53ae8e20b8a51b3a4559a3e7e5651dd204a0` as an ancestor.
- Review finding: a held poll for session A survived `UploadScreen` unmount/session replacement. Its late completion unconditionally updated the global provider/session storage and routed to `/results`, replacing active session B.
- RED: `npm run test:smoke -- task10-semantic-ui.spec.ts --grep "ignores a stale semantic completion" --reporter=list` -> expected `2 failed` on desktop/mobile; both observed `new-review-session` replaced by `old-review-session`.
- Fix: the request and poll helpers accept a backwards-compatible optional `AbortSignal`; retry delays are abortable; `UploadScreen` invalidates the poll generation on unmount or session-ID change and guards stale global update, navigation, error display, and polling-ref cleanup. Cancellation is silent.
- Focused GREEN: the same command -> `2 passed (7.3s)`. Full `task10-semantic-ui.spec.ts` -> `26 passed (18.9s)`, retaining normal completion routing, transient retry/backoff, failure messaging, reload resume, and semantic-result presentation.
- Frontend regression: `npm run test:smoke -- --reporter=list` -> `42 passed, 10 skipped in 39.1s`; skipped cases were opt-in ACTUAL/public lanes. `npm run typecheck` -> PASS. `npm run build` -> PASS (Next.js 16.3.4 compiled, typed, and generated 8 static pages).
- Fresh TASK10 local ACTUAL: guarded isolated `npm run test:smoke -- task10-actual-semantic.spec.ts --project=desktop --reporter=list` -> `1 passed (1.2m)`. Session `d5c955c6-9507-446b-a26e-426ba45c7c35`; profile `76547978-48ea-4134-b45b-4391d558d1db`; harness-asserted ledger `EXTRACT=1`, `PLAN=0`, `SEMANTIC=4`. Positive, missing, recheck, and injection runs each ended `COMPLETE / REVIEW_REQUIRED / REVIEW`; missing coverage was `FULL`; no semantic PASS/BLOCKER occurred.
- TASK08 ACTUAL was not rerun because its synchronous deterministic path does not use this poller. Its existing session, PlanSet, `EXTRACT=1 / PLAN=1 / SEMANTIC=0`, and `semantic_review=null` evidence remain unchanged.
- Backend tests were **NOT RERUN** because this fix changes only the frontend request/poll lifecycle and no backend contract.
- Runtime metadata: requested override `gpt-5.6-sol` / `high`; configured override `gpt-5.6-sol` / `high` from controller spawn-tool evidence; actual/agent-observed implementer runtime UNKNOWN; token usage UNKNOWN. The configured override is not proof of the actual runtime. The ACTUAL provider was the existing ChatGPT-authenticated Codex CLI configured with `gpt-5.6-sol` / `high`.
- Public TASK09/TASK10 ACTUAL remain **NOT TESTED** after the previously recorded HTTP 404. No new public request, service start/replacement, deployment, push, PR, merge, paid credit, key, account, model setting, or global configuration change occurred. CI URLs: none.
- Changed scope: `frontend/components/screens.tsx`, `frontend/lib/api.ts`, `frontend/lib/poll-session.ts`, `frontend/tests/task10-semantic-ui.spec.ts`, refreshed bounded `artifacts/task10/actual-semantic-e2e.json`, and evidence documentation only.
- Delivery status: fix implemented and locally verified; **DO NOT MERGE pending Astra re-review and Product Lead review**. The exact new commit SHA is reported after commit because a commit cannot truthfully contain its own SHA.
