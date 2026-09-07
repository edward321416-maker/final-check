# Tasks

## TASK 01 — Preserved baseline
- [x] Five-screen skeleton, contracts, mock fixtures and browser interactions.
- [x] Baseline rerun before TASK 02: typecheck/build, 8 browser tests, 16 backend tests.
- [x] Baseline preserved as commit 7bc3aeb and artifacts/task01-baseline/.

## TASK 02 — Frozen Validator v1.5 Integration + Real Demo Fixtures
- [x] Verify original source SHA before integration.
- [x] Preserve all frozen source/policy/reference bytes.
- [x] Install actual runtime imports and execute import/ffprobe smoke.
- [x] Adapt original native input/output in Python without source edits.
- [x] Generate and independently audit new 61s/45s actual packages.
- [x] Execute real broken/fixed acceptance; save raw and adapted outputs separately.
- [x] Real browser uploads and rechecks; 8 browser tests passed.
- [x] Safety/status/error/scan invariants; 26 backend tests passed.
- [x] Migrate status enum to BLOCKED / REVIEW_REQUIRED / READY.
- [x] Visibly disclose absent Vision and generic announcement extractor.
- [x] Create dedicated public FINAL CHECK repository.
- [x] Push source through the dedicated public repository and normal delivery PR #1.
- [x] Document actual execution, tests, limitations and source integrity.

## Future work requiring scoped input
- TASK08 is delivered below for Product/Business Lead PR review. Select the next priority only after that review; do not preselect deployment, semantic, Vision/OCR or file-format expansion.
- Select a Vision provider only with required authorization and test it separately.
- Confirm production storage, deployment, retention and supported announcement profiles.
- Historical 39-case reproduction requires the exact original corpus; do not substitute new fixtures.

## TASK 03 — Generic Announcement → Requirement Profile Integration
- [x] Verify main e1fab59 and unchanged frozen SHA before edits; work on codex/task-03-generic-requirement-profile.
- [x] Rerun unchanged baseline: 26 backend / 8 browser passed.
- [x] Add separate Python/TypeScript generic canonical schema and injectable provider boundary.
- [x] Implement ACTUAL local-rule extraction with explicit no-AI labeling and evidence/schema/atomicity gates.
- [x] Accept text and actual text-PDF; scanned/unreadable input generates no rules.
- [x] Human edit/delete/review/approve → explicit profile CONFIRMED; original evidence and history preserved.
- [x] Hand off confirmed profile to generic orchestration with REVIEW/EXTERNAL only; no fake PASS/BLOCKER/READY.
- [x] Execute all updated tests: 47 backend, 14 browser; typecheck and production build pass.
- [x] Verify frozen directory after tests; preserve original CSS and five routes.
- [x] Record ACTUAL TEST / SELF-BENCHMARK / SIMULATED / NOT TESTED and first browser failure evidence.
- [x] Commit/push implementation 690200c and create delivery PR #2; now MERGED at 81bf2551c5967836d3e54869de2e86261428c78e.

## TASK 04 — Independent Extractor Reality Check

- [x] Reconfirm merged PR2, fetch/synchronize clean main and create the requested branch.
- [x] Verify frozen validator and TASK03 baseline source hashes before execution.
- [x] Capture eight real independent announcements with original bytes and documented input scopes.
- [x] Author 173 atomic Gold before output; freeze hashes/timestamp and commit before running baseline.
- [x] Execute unchanged local-rules-v1; preserve failed harness attempt separately from valid raw outputs.
- [x] Manually score all 211 candidates and all 173 Gold; no partial/duplicate full credit.
- [x] Measure recall, precision, modality, exact/semantic evidence, atomicity, hallucinations and blockers.
- [x] Record broad keyword/condition/table failures and 35 repeated-quote anchor mismatches; no tuning.
- [x] Backend47, browser14, typecheck/build and frozen before/after checks pass.
- [x] Record GO direction and AI-first comparison recommendation with same-agent annotation limits.
- [x] Publish benchmark commit92b7e50 and PR #3; verified OPEN, left unmerged for Product/Business Lead review.
- [x] TASK05 scope authorized by Product/Business Lead after PR3 merged at 0125f05.

## TASK 05 — Blind AI-First Extractor Comparison

- [x] Fetch and synchronize clean main; verify Gold173 and frozen hashes.
- [x] Freeze one prompt/schema/candidate before output; eight fresh isolated invocations.
- [x] Preserve354 actual RAW candidates,237 GATED candidates and all execution traces.
- [x] Apply unchanged TASK03 gate and TASK04 scoring; Gold and local extractor unchanged.
- [x] Score every candidate/Gold pair; measurement PASS, locked AI candidate STOP.
- [x] Backend47, browser14, TypeScript/build, diff and before/after integrity checks pass.
- [x] Publish TASK05 PR #4 (https://github.com/edward321416-maker/final-check/pull/4); merged at d5bbddac39645aa11076575e81d976579eba5d9f.

## TASK 06 — Two-Stage AI Extraction MVP Integration

- [x] Start from merged TASK05 main and verify Gold173 plus every locked TASK05/frozen hash.
- [x] Add separate Stage1 generator and Stage2 semantic-reviewer provider boundaries.
- [x] Run the actual local Codex provider with versioned Stage1/Stage2 prompts and provenance.
- [x] Enforce deterministic schema, enum, unique-ID, source, exact-evidence and offset gates.
- [x] Support KEEP/REVIEW/DROP, organizer/prize/form-label filtering, duplicate links and condition review.
- [x] Replace the 100-candidate all-or-nothing failure with visible overflow, 50-item batches and a 500 hard ceiling.
- [x] Preserve successful Stage2 batches and retry only failures; never silently fall back to local rules.
- [x] Keep AI blockers provisional and non-authoritative until explicit human approval.
- [x] Preserve edit/delete/approve/full-source confirmation and REVIEW/EXTERNAL-only generic handoff.
- [x] Run actual public C03 E2E: real Stage1/Stage2, UI review, profile confirmation, upload and generic results.
- [x] Pass 59 backend, 14 standard browser and 1 actual-AI browser tests; typecheck/build/diff and frozen integrity pass.
- [x] Product Lead invoked the Issue-based GitHub task flow; final delivery and normal merge are tracked by Issue #6.

## TASK 07 — Restart-Safe Durable Runtime MVP

- [x] Verify merged PR #7 baseline `07cd3e6`, clean main, Gold173 and frozen hashes.
- [x] Create Issue #8 before branch `issue/8-restart-safe-durable-runtime`.
- [x] Add Python `sqlite3` session/job storage and application-owned durable artifact paths.
- [x] Persist canonical profile, review, confirmation, validation and current-job state without pickle.
- [x] Add explicit job states, provider provenance, attempts and safe error categories.
- [x] Checkpoint Stage1, deterministic gate, each Stage2 batch and finalization.
- [x] Recover stale RUNNING jobs as RETRYABLE and resume without repeating completed work.
- [x] Enforce operation idempotency, three explicit attempts and active/retryable TTL protection.
- [x] Pass an actual backend process stop/start acceptance and simulated checkpoint faults.
- [x] Preserve TASK06 local Codex and human-safety contracts; no generic verifier or deployment work.
- [x] Product Lead merged TASK07 PR #9 at `fa3108db4074499ddefffca53e34f51bd7f95395`.

## TASK 08 — Typed Verifier Compiler + Deterministic Checker Engine MVP

- [x] Verify merged TASK07 baseline `fa3108d`, clean main, Gold173 and frozen hashes.
- [x] Create Issue #10 before branch `issue/10-typed-verifier-compiler` using `github-task-flow`.
- [x] Add a submission-independent `VerificationPlanner` boundary using the existing authenticated Codex CLI.
- [x] Freeze `task08-planner-v1` and its structured-output schema before the first actual planner output.
- [x] Add a closed typed plan DSL, parameter provenance and deterministic source-grounding gate.
- [x] Implement FILE_PRESENCE, FILE_COUNT, FILE_NAME, FILE_TYPE, FILE_SIZE, PDF_PAGE_COUNT and VIDEO_METADATA.
- [x] Keep `generic_review` review-only and add evidence-required `generic_verifier` results plus a separate generic readiness policy.
- [x] Persist PlanSets through TASK07 storage, recover interrupted planner state, reuse plans across submissions and invalidate them on profile/source changes.
- [x] Run ACTUAL public C01 exact-excerpt E2E with actual Stage1/Stage2/planner, 61-second BLOCKED result and 45-second READY result using one PlanSet.
- [x] Pass 134 backend tests, 16 standard browser tests, one existing TASK06 actual-AI regression and one TASK08 actual product E2E; typecheck/build/diff pass.
- [x] Preserve Gold173, TASK04/TASK05 scores and frozen Validator bytes; no benchmark, prompt tuning, deployment, Vision/OCR or new format work.
- [ ] Product Lead reviews the TASK08 PR, which remains OPEN / NOT MERGED.
