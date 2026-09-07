# FINAL CHECK judging runbook

Submission deadline: **2026-09-20 23:59:59 KST**
Judging period: **2026-09-21 through 2026-10-05**

Public URL: `https://uncoy-joelle-macrodont.ngrok-free.dev`

> ngrok Free 특성상 첫 접속 시 ngrok 안내 페이지가 한 번 표시될 수 있습니다. Visit Site를 누르면 FINAL CHECK로 이동합니다.

## Before judging

- Keep the host PC awake and online; start the local production runtime with `scripts/start-public-judge.ps1`.
- Confirm the public health endpoint, Codex CLI `gpt-5.6-sol` with high reasoning, local SQLite, frozen Validator, ffprobe, and public guard.
- Confirm the reviewed commit and no pending code or prompt changes.
- Use only the public C01 excerpt and synthetic/generated TASK08 media. Do not enter personal data or confidential submissions.

## ACTUAL public acceptance

1. Open the ngrok HTTPS URL in a fresh browser without a bypass header. Confirm the one-time ngrok notice and use `Visit Site` to reach FINAL CHECK.
2. Enter the C01 exact excerpt containing the 60-second video rule.
3. Complete Codex Stage1 and Stage2. Review retained requirements and confirm the full profile.
4. Complete the Codex Planner and record its PlanSet ID.
5. Upload the actual 61-second MP4. Require announcement evidence, submission evidence, BLOCKER, and final BLOCKED.
6. In the same session, replace it with the actual 45-second MP4. Require PASS and READY.
7. Confirm Planner was not called again and both checks used the same PlanSet ID.
8. Save sanitized health, session/result, and screenshot evidence under `artifacts/task09/`.

The first-visit smoke and application E2E are separate evidence. `public-first-visit.json` covers an empty browser context, no `ngrok-skip-browser-warning` header, the notice, and the `Visit Site` transition. `public-e2e.json` uses the bypass header and covers only the application flow after the notice.

Classify the public ngrok first visit, Codex calls, ffprobe, and actual media validation as ACTUAL. Unit/integration/browser safety tests are SELF. Injected failure tests are SIMULATED. A browser on a different network, cloud failover, production SLA, DDoS resilience, large traffic, Vision/OCR, new formats, auth, payments, and backups are NOT TESTED.

## During judging

- Keep the host PC and network continuously available. There is no cloud failover.
- Check public health and ngrok usage daily; ngrok Free outbound transfer is limited to 1 GB/month.
- Do not deploy prompt, schema, dependency, feature, or documentation changes during the judging freeze.
- Keep the reviewed version online through the end of 2026-10-05, then stop the public tunnel.
