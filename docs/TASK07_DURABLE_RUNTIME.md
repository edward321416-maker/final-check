# TASK07 Restart-Safe Durable Runtime

TASK07 keeps the TASK06 extraction order and local Codex provider while making
the single-node runtime survive a backend process restart.

## Storage boundary

`SessionStore`, `JobStore`, and `ArtifactStore` are small typed protocols. The
default implementation uses Python `sqlite3` for canonical JSON metadata and an
application-owned filesystem tree for bytes. Set `FINAL_CHECK_DATA_DIR` to move
the whole runtime. Without it, the local default is `.final-check/runtime/`:

```text
.final-check/runtime/
├── runtime.sqlite3
└── sessions/<session-id>/
    ├── announcement/source.bin
    ├── submission/<validated-user-filename>
    └── run-<revision>-raw.json
```

This directory is excluded from Git. Filenames pass the existing basename,
extension, length, and invalid-character checks before being written. Session
directories use application-generated IDs; cleanup refuses paths outside the
owned sessions root. Codex authentication, tokens, cookies, environment values,
and provider stderr are never fields in the durable models.

## Job and checkpoint behavior

One unique job identity is `(session_id, profile_id, profile_version, job_kind)`.
Repeated requests reuse that row. States are `PENDING`, `RUNNING`, `SUCCEEDED`,
`RETRYABLE`, and `FAILED`. The job records timestamps, attempt, safe error
category, provider prompt provenance, a typed profile checkpoint, and completed
Stage2 batch indexes.

The durable boundaries are `STAGE1_COMPLETE`, `GATE_COMPLETE`,
`STAGE2_BATCH_N_COMPLETE`, and `FINALIZED`. Each successful boundary saves both
the job and recoverable profile state. A retry reads the checkpoint: completed
Stage1 and completed Stage2 batches are skipped. Three explicit attempts are
allowed. There is no automatic retry loop; authentication failure remains a safe
category and waits for user action.

At application startup, a `PENDING` or `RUNNING` row left by a dead process
becomes `RETRYABLE`. Its session exposes the recovered job and a `REVIEW_REQUIRED`
pipeline status. It never becomes confirmed, PASS, or READY through recovery.

## Retention and supported topology

The one-hour TTL remains. Expired sessions and their application-owned artifacts
are removed only when they have no `PENDING`, `RUNNING`, or `RETRYABLE` job and no
active process-local operation lock. The maximum stored-session count remains
100.

This is a restart-safe, single-node, single-backend-process MVP. SQLite and the
process-local lock are not claimed to coordinate multiple workers or hosts.
Cloud deployment, Redis/Celery, provider selection, Vision/OCR, and generic
submission verification remain outside TASK07.
