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
