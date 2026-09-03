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
- TASK 04: independently benchmark generic extraction with separately authored announcements/gold, including modality, evidence, atomicity and omissions. No accuracy claim from TASK 03.
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
- [x] Commit/push implementation 690200c and create delivery PR #2 (OPEN, not merged).
