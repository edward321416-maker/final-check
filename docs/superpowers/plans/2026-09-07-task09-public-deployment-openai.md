# TASK09 Zero-Cost Public Deployment Plan

## Goal and baseline

Expose the current local production build through the account-assigned ngrok Free HTTPS development domain and run the real TASK08 acceptance through the public URL. Keep the existing ChatGPT-authenticated Codex CLI for Stage1, Stage2, and Planner. Preserve human confirmation, the deterministic verifier, local SQLite/filesystem state, ffprobe, Gold173, all prompt bytes, and the frozen Validator.

- Baseline main: `ad08ccb3a2c8dbf07dbfed6eae2c2e6a0d64e111`
- Issue: `#12`
- Branch: `issue/12-public-deployment-openai` (retained because it is not yet shared)
- Public URL: `https://uncoy-joelle-macrodont.ngrok-free.dev`
- AI provider: existing Codex CLI
- Model/reasoning: `gpt-5.6-sol` / `high`
- Runtime: one local FastAPI worker, one Next.js production server, local SQLite/filesystem
- Railway Hobby and OpenAI API billing: canceled
- OpenAI Responses production provider: deferred

## Implementation

1. Remove the unshared OpenAI Responses adapter, Railway Dockerfiles, and Railway-specific health and documentation contracts.
2. Retain the durable public guard, smaller public upload limits, no-store/security headers, robots exclusion, and privacy boundary.
3. Make production health require the existing authenticated Codex CLI, exact model/reasoning, local writable storage, frozen Validator, ffprobe, and enabled public guard.
4. Add safe PowerShell start/stop scripts for the local production servers and the fixed ngrok development domain. Keep process manifests and logs in ignored runtime storage; never copy or print credentials.
5. Allow Playwright to target an explicit public base URL and add a TASK09 actual test that saves separate sanitized evidence.
6. Replace paid-cloud runbooks with the host-PC availability, restart, judging freeze, ngrok quota, and no-SLA procedures.

## Verification and delivery

1. Run focused TASK09 tests, full backend tests, TASK08 regression, TypeScript typecheck, and a fresh production build.
2. Start the public runtime and verify the public health response and security/no-store headers.
3. Run actual public Codex Stage1, Stage2, human-confirmed profile, Codex Planner, actual 61-second BLOCKED, and same-PlanSet 45-second READY.
4. Restart the recorded local processes and confirm health plus durable runtime recovery.
5. Record sanitized ACTUAL/SELF evidence. Confirm prompt, Gold, and frozen Validator hashes remain unchanged.
6. Amend the unpushed Lore commit, push exactly one commit, and open a PR that remains OPEN / NOT MERGED.

## Limitations and stop conditions

Judge availability depends on the host PC and network. There is no cloud failover, ngrok Free outbound transfer is limited to 1 GB/month, and no production SLA is claimed. Stop and report BLOCKED if the assigned development domain, authenticated Codex CLI, ffprobe, public health, public ACTUAL flow, or same-PlanSet result is unavailable. Vision/OCR, semantic submission verification, new formats, authentication, payment, and high-availability work remain deferred.
