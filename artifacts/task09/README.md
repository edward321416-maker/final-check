# TASK09 evidence index

Current state: **ACTUAL PUBLIC MVP PASS** on the zero-cost local/ngrok deployment path.

- `deployment-metadata.json`: local production runtime, fixed public domain, tool versions, and operating limits.
- `public-health.json`: public production health response with the Codex, ffprobe, storage, guard, and frozen engine status.
- `provider-usage.json`: actual Stage1, Stage2, and Planner invocation summary. Codex CLI does not expose API token accounting.
- `public-e2e.json`: actual public Stage1 -> Stage2 -> human confirm -> Planner -> deterministic 61s BLOCKED -> same PlanSet 45s READY flow.
- `restart-recovery.json`: actual process restart with the same durable session and PlanSet restored.
- `local-verification.json`: regression suite and frozen-asset integrity summary.
- `screenshots/`: actual public 61-second BLOCKED and 45-second READY UI evidence.

The public endpoint depends on the host PC and network, has no cloud failover or production SLA, and is subject to the ngrok Free 1 GB/month outbound limit. Evidence is sanitized and contains no secrets, authorization headers, personal data, confidential submissions, or full announcement prompts.
