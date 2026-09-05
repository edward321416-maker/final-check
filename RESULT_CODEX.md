# RESULT_CODEX — TASK 07

Date: 2026-09-05 (Asia/Seoul)

Baseline main: `07cd3e6587efd47661f2e42f72574f569bce9094` (TASK06 PR #7 merge commit).
Issue: [#8](https://github.com/edward321416-maker/final-check/issues/8).
Branch: `issue/8-restart-safe-durable-runtime`.

## Verdict

- TASK07: **PASS**.
- FINAL CHECK: **GO**.
- Durable Runtime: **GO**.
- Local Codex Provider: **KEEP**.
- Single-node Deployability: **READY_FOR_DEPLOYMENT_TASK**.
- Production AI Provider: **NOT_SELECTED**.

## Durable architecture

- `SessionStore`, `JobStore`, and `ArtifactStore` define the minimal storage
  boundary. The default metadata implementation is Python standard-library
  `sqlite3`; model payloads use canonical Pydantic JSON and never pickle.
- `FINAL_CHECK_DATA_DIR` configures the root. The local default is
  `.final-check/runtime/`, excluded from Git. Metadata is in
  `runtime.sqlite3`; announcement/submission/raw artifacts are under
  `sessions/<application-session-id>/`.
- Validated user basenames are stored only inside the application session tree.
  Announcement replacement is atomic. Cleanup resolves and verifies the owned
  session parent before removal.

## Durable job behavior

- States: `PENDING`, `RUNNING`, `SUCCEEDED`, `RETRYABLE`, `FAILED`.
- Stored fields include job/session/profile identity, job kind, status, stage,
  attempt, timestamps, safe error category, TASK06 provider provenance,
  completed Stage2 batch indexes, and the typed profile checkpoint.
- One database uniqueness constraint covers
  `(session_id, profile_id, profile_version, job_kind)`. Duplicate extract
  requests reuse the existing job.
- Checkpoints: `STAGE1_COMPLETE`, `GATE_COMPLETE`,
  `STAGE2_BATCH_N_COMPLETE`, `FINALIZED`. Retry skips a completed Stage1 and
  every committed Stage2 batch.
- Startup converts abandoned `PENDING`/`RUNNING` jobs from a dead process to `RETRYABLE` and
  exposes `PROCESS_RESTART` plus a user-controlled resume action. There is no
  automatic loop. Three explicit attempts are allowed; authentication failure
  is stored only as a safe category.
- One-hour cleanup removes safe expired metadata and artifacts. A process-active
  session or a session with a PENDING/RUNNING/RETRYABLE job is retained.

## Human safety persistence

- Raw candidates, gated IDs, Stage2 reviews, retained requirements, edit/delete/
  approval history, source acknowledgement and CONFIRMED status round-trip
  through SQLite.
- An AI-proposed BLOCKER remains `authoritative=false` after reconstruction.
  Recovery and provider failure cannot confirm a profile or produce PASS/READY.
- TASK06 prompts, model choice, deterministic gates and mandatory human
  confirmation are unchanged.

## Tests and evidence

- Backend: **77 passed** in the final suite: existing 59 plus 18 new
  TASK07 persistence/recovery/security cases. The final JUnit is stored under
  `artifacts/task07/backend-junit.xml`.
- TASK07 TDD: the new test module first failed collection because the durable
  job module did not exist, then passed after implementation.
- Restart acceptance: **ACTUAL LOCAL TEST** starts a backend process, creates a
  custom session and meaningful announcement profile, stops the process,
  restarts against the same data directory, and retrieves the same profile.
- AI recovery: **SELF / SIMULATED** fault injection verifies stale RUNNING
  recovery, no Stage1 replay, no completed Stage2-batch replay, duplicate-job
  reuse, retry limit, TTL protection and absence of provider secret/error text.
- Standard browser: **14 passed, 2 opt-in skipped** on desktop/mobile. Existing
  real uploads, human review, reload and five-screen flows remain intact.
- Actual local AI: **1 passed** in 1.9 minutes. The C03 runtime regression used
  the existing ChatGPT-authenticated Codex CLI once: job `SUCCEEDED / FINALIZED`,
  attempt 1, completed batch `[0]`, 14 RAW, 14 GATED, 12 retained, human-confirmed
  handoff, actual submission upload and safe `REVIEW_REQUIRED` generic result.
- TypeScript typecheck: **PASS**. Production build: **PASS**.
- `git diff --check`: recorded in final delivery evidence.

## Frozen integrity

- TASK04 Gold count: **173**.
- Gold manifest SHA-256:
  `035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89`.
- Frozen Validator SHA-256 before/after:
  `4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11`.
- No Gold, benchmark score, prompt, model or frozen Validator file changed.

## Evidence classification

- **ACTUAL:** GitHub baseline verification; actual backend process stop/start;
  actual SQLite/filesystem restore; 14 standard browser tests with actual local
  uploads/validator; one actual local Codex product E2E.
- **SELF:** canonical serialization, idempotency, checkpoint, retention and
  safety tests authored and executed in this task.
- **SIMULATED:** dead-process RUNNING row, provider interruption, Stage2 batch
  interruption, secret-bearing exception and retry-limit injections.
- **NOT TESTED:** actual OS kill during the narrow interval after provider return
  but before checkpoint commit; multiple backend workers/nodes; cloud volume,
  backup/restore, public deployment, production provider availability, Vision/
  OCR and generic submission verification.

## Limits and next task

This is a restart-safe **single-node, single-backend-process** MVP. SQLite does
not coordinate several workers. A provider call whose response was not committed
may repeat after restart; committed Stage1 and Stage2 batches do not.

The next recommended scope after Product Lead review and merge is **TASK08 —
Generic Verifier Engine**. TASK08 was not started here.

## Delivery

- One Korean Lore commit will reference Issue #8.
- The TASK07 PR will be created against `main` and intentionally left
  **OPEN / NOT MERGED** for Product Lead diff and runtime-evidence review.
