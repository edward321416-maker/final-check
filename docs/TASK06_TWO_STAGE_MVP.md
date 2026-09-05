# TASK06 Two-Stage AI Extraction MVP

The generic announcement path uses a provisional two-stage pipeline:

1. Stage 1 generates applicant-facing candidate requirements.
2. A deterministic gate validates schema, enums, unique IDs, source hashes, exact quotes and offsets.
3. Stage 2 assigns KEEP, REVIEW or DROP with a reason and provider provenance.
4. A human edits, deletes or approves every retained item and acknowledges the full source.
5. Only the confirmed profile enters the existing generic upload path, which returns REVIEW or EXTERNAL.

The default local MVP provider is the existing ChatGPT-authenticated Codex CLI. Long AI calls run
as a background extraction and the browser polls short status requests, avoiding the frontend proxy's
long-request timeout. Set `FINAL_CHECK_AI_PROVIDER=local-fallback` only for the explicitly labelled
local-rule suggestion path used by deterministic regression tests.

Candidate sets above 100 are marked `OVERFLOW_REVIEW` and sent to Stage 2 in batches of 50. The
pipeline preserves successful batches for retry and has a hard ceiling of 500. It never silently keeps
only the first 100 candidates. Provider errors remain unconfirmed and cannot activate validation.

Run the standard local suite from the existing backend/frontend environments. The real-provider E2E
is opt-in because it uses the signed-in local provider:

```powershell
$env:TASK06_ACTUAL_AI='1'
$env:FINAL_CHECK_AI_PROVIDER='codex'
cd frontend
npx playwright test tests/task06-actual-ai.spec.ts --project=desktop
```

The actual acceptance artifacts are under `artifacts/task06/`. They use public TASK04 source C03 as a
representative product input and are not accuracy benchmark results.
