# RESULT_CODEX — TASK 06

Date: 2026-09-05 (Asia/Seoul). Repository: `edward321416-maker/final-check`.
Branch: `codex/task-06-two-stage-ai-extraction-mvp`.
Baseline main: `d5bbddac39645aa11076575e81d976579eba5d9f` (TASK05 PR #4 merge commit).
The previous TASK05 report is preserved at `artifacts/task05-baseline/RESULT_CODEX_TASK05.md`.

## GITHUB BASELINE

- PR #4 was verified merged before work began.
- Local main was synchronized to `d5bbddac39645aa11076575e81d976579eba5d9f` and the worktree was clean.
- TASK05 Gold count and all locked hashes matched before implementation.

## TASK06 STATUS

**PASS — safe two-stage local MVP integration completed.** This task did not create Gold,
rescore TASK04/05, compare models, or tune prompts against benchmark results.

## ARCHITECTURE

```text
Announcement
  → Stage 1 RequirementGenerator (provisional candidates)
  → deterministic schema/evidence/offset/ID gate
  → Stage 2 SemanticRequirementReviewer (KEEP / REVIEW / DROP)
  → human edit/delete/approve and whole-source acknowledgement
  → CONFIRMED Requirement Profile
  → existing generic upload path (REVIEW / EXTERNAL only)
```

Provider-specific execution is isolated behind `RequirementGenerator` and
`SemanticRequirementReviewer`. The application core does not call Codex CLI directly.
Actual calls receive the prompt, output schema and current source/candidate payload in an
ephemeral directory. The copied authentication transport is deleted after each call and is
never stored in product artifacts.

## PROVIDERS

- **ACTUAL LOCAL AI PROVIDER:** existing ChatGPT-authenticated Codex CLI, requested
  `gpt-5.6-sol` with high reasoning. This is a local MVP adapter, not a production provider decision.
- **SIMULATED / SELF tests:** explicit fake providers and fault injection cover safety boundaries.
- **Explicit fallback:** local rules remain available only when
  `FINAL_CHECK_AI_PROVIDER=local-fallback`; the UI labels this path and requires human review.
  Provider failure never silently changes to local rules.

Prompt provenance:

- Stage 1 `task06-stage1-v1`: `52b226089eddf6fb109ab07f676110c7dea48c602397a7d6c283384e3be4d7f4`
- Stage 2 `task06-stage2-v1`: `be838b1ef8d57f921147a3dfb993fa3237fb56dd766b825c883b644aa131163f`

## OVERFLOW

- Normal overflow threshold: more than 100 raw candidates.
- Stage 2 batch size: 50.
- Hard ceiling: 500 raw candidates.
- The SELF 117-candidate case retained and processed all 117 candidates in batches
  `[50, 50, 17]`; it did not collapse to zero or truncate at 100.
- Overflow is visible as `OVERFLOW_REVIEW`. Partial batch success is preserved and only failed
  batches are retried. More than 500 produces explicit `EXTRACTION_ERROR`, cannot become READY,
  and does not silently present a partial confirmed profile.

## BLOCKER SAFETY

Every AI candidate is `authoritative=false`. An AI-proposed BLOCKER is displayed as
`PROVISIONAL_BLOCKER` and cannot block a submission before separate human approval.
Stage 2 unsupported evidence becomes REVIEW. Only a human-approved requirement becomes
`CONFIRMED` and `authoritative=true`; every retained item plus full-source acknowledgement is
required before whole-profile confirmation.

## ACTUAL DEMO

One representative public announcement was run as product acceptance, not a benchmark:

- Source: TASK04 C03, `https://kibs.kookmin.ac.kr/notice/91`
- Source SHA-256: `5c93e8ab7506e074db8bd983f078f96e6fc9e60cf33e48a53a571640d99f2db6`
- Actual Stage 1: 24 raw candidates; deterministic gate retained 24.
- Actual Stage 2: KEEP 12, REVIEW 4, DROP 8; 16 retained for human review.
- Human flow: 3 edits, 1 delete, 15 approvals, full-source acknowledgement, profile CONFIRMED.
- Actual submission upload: 15 generic results, 14 REVIEW and 1 EXTERNAL;
  `validation_complete=false`, session `REVIEW_REQUIRED`, no PASS/BLOCKER.
- Evidence: `artifacts/task06/actual-e2e-manifest.json`, raw session JSON files and browser screenshot.

## PROVIDER FAILURE

Unavailable provider, timeout, nonzero exit, invalid JSON/schema and Stage 2 batch failure are
explicit error/review states. Safe diagnostic categories contain no provider output or secrets.
Completed Stage 2 batches and raw candidates remain available when another batch fails. No error
path activates validation or produces READY/PASS.

## TESTS

- Backend: **59 passed**, including the pre-existing 47 and 12 TASK06 safety test cases.
- Browser regression: **14 passed, 2 opt-in actual-AI cases skipped** in the standard suite.
- Actual AI browser E2E: **1 passed** on desktop with real Stage 1 and Stage 2 calls.
- TypeScript: PASS.
- Production build: PASS.
- `git diff --check`: PASS.
- These are **ACTUAL LOCAL TEST** results. Hosted GitHub Actions were not run and no CI PASS is claimed.

## SOURCE INTEGRITY

- Gold count: **173**.
- Gold manifest SHA-256:
  `035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89`.
- Frozen Validator SHA-256:
  `4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11`.
- TASK05 prompt/schema hashes remain unchanged. TASK04/05 historical scores were not recalculated.

## CLASSIFICATION

- **ACTUAL:** public C03 source, real local Codex Stage 1/2 calls, backend/frontend review,
  human interaction sequence, file upload and generic REVIEW/EXTERNAL handoff.
- **SELF:** TASK06 synthetic 117/501-candidate and contract fixtures.
- **SIMULATED:** mock semantic decisions, provider errors and partial-batch fault injection.
- **NOT TESTED:** production AI provider/SLA, independent human usability/adjudication, Vision/OCR,
  automatic generic submission verification, deployment, multi-worker durability and hosted CI.

## DIRECTION

- FINAL CHECK: **GO**.
- Two-stage extraction: **GO for local MVP**.
- Stage 1 AI: **GO for provisional local MVP candidates**.
- Stage 2 semantic reviewer: **GO for local MVP filtering; human review remains required**.
- Human confirmation: **REQUIRED**.
- AI pre-confirmation BLOCKER authority: **NOT_ALLOWED**.
- Candidate overflow: preserve all candidates through 500, review in batches of 50, show
  `OVERFLOW_REVIEW` above 100, preserve successful batches, fail explicitly above 500.

## LIMITATIONS AND NEXT RECOMMENDATION

The provider uses a signed-in local Codex installation and in-memory single-process sessions.
It is not a production service contract. Vision/OCR, an automatic generic verifier, deployment,
authentication and durable job storage remain outside TASK06 and unimplemented.

The next scoped task should evaluate and select a production execution/job boundary, including
durable status and retry behavior, without changing frozen validation or starting Vision and
generic-verifier work at the same time. Product Lead review is required before that task begins.
